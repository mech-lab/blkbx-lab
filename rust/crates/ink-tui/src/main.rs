use std::io;
use std::path::{Path, PathBuf};

use clap::{Parser, Subcommand};
use crossterm::event::{self, Event, KeyCode, KeyEventKind, KeyModifiers};
use crossterm::execute;
use crossterm::terminal::{
    disable_raw_mode, enable_raw_mode, EnterAlternateScreen, LeaveAlternateScreen,
};
use ratatui::backend::CrosstermBackend;
use ratatui::layout::{Constraint, Direction, Layout};
use ratatui::style::{Color, Modifier, Style};
use ratatui::text::{Line, Span};
use ratatui::widgets::{Block, Borders, List, ListItem, Paragraph, Wrap};
use ratatui::{Frame, Terminal};

#[derive(Parser)]
#[command(name = "ink-tui", about = "Zero-JS independent INK receipt verifier")]
struct Cli {
    #[command(subcommand)]
    command: Option<Commands>,
}

#[derive(Subcommand)]
enum Commands {
    /// Verify directly without entering the terminal UI.
    Verify {
        #[arg(long)]
        receipt: PathBuf,
        #[arg(long)]
        manifest: Option<PathBuf>,
        #[arg(long)]
        controls: Option<PathBuf>,
        #[arg(long)]
        trust_registry: Option<PathBuf>,
        #[arg(long)]
        revocation_list: Option<PathBuf>,
        #[arg(long)]
        policy: Option<PathBuf>,
        #[arg(long)]
        pinned_key: Option<String>,
    },
}

#[derive(Clone, Copy)]
enum FieldId {
    Receipt,
    Manifest,
    Controls,
    TrustRegistry,
    RevocationList,
    Policy,
    PinnedKey,
}

impl FieldId {
    fn all() -> &'static [Self] {
        &[
            Self::Receipt,
            Self::Manifest,
            Self::Controls,
            Self::TrustRegistry,
            Self::RevocationList,
            Self::Policy,
            Self::PinnedKey,
        ]
    }

    fn label(self) -> &'static str {
        match self {
            Self::Receipt => "Receipt path",
            Self::Manifest => "Manifest path",
            Self::Controls => "Controls path",
            Self::TrustRegistry => "Trust registry path",
            Self::RevocationList => "Revocation list path",
            Self::Policy => "Verify policy path",
            Self::PinnedKey => "Pinned public key",
        }
    }
}

struct App {
    values: Vec<String>,
    selected: usize,
    result: String,
}

impl App {
    fn new() -> Self {
        Self {
            values: vec![String::new(); FieldId::all().len()],
            selected: 0,
            result: "Press F5 to verify, q to quit, tab to move fields.".to_string(),
        }
    }

    fn value(&self, field: FieldId) -> &str {
        &self.values[field as usize]
    }

    fn value_mut(&mut self, field: FieldId) -> &mut String {
        &mut self.values[field as usize]
    }

    fn selected_field(&self) -> FieldId {
        FieldId::all()[self.selected]
    }

    fn run_verify(&mut self) {
        match verify_paths(
            path_or_none(self.value(FieldId::Receipt)),
            path_or_none(self.value(FieldId::Manifest)),
            path_or_none(self.value(FieldId::Controls)),
            path_or_none(self.value(FieldId::TrustRegistry)),
            path_or_none(self.value(FieldId::RevocationList)),
            path_or_none(self.value(FieldId::Policy)),
            string_or_none(self.value(FieldId::PinnedKey)),
        ) {
            Ok(report) => {
                self.result = serde_json::to_string_pretty(&report).unwrap_or_else(|err| {
                    format!("failed to render verification report: {err}")
                });
            }
            Err(err) => {
                self.result = format!("{err}");
            }
        }
    }
}

fn main() -> Result<(), Box<dyn std::error::Error>> {
    let cli = Cli::parse();
    if let Some(Commands::Verify {
        receipt,
        manifest,
        controls,
        trust_registry,
        revocation_list,
        policy,
        pinned_key,
    }) = cli.command
    {
        let report = verify_paths(
            Some(receipt.as_path()),
            manifest.as_deref(),
            controls.as_deref(),
            trust_registry.as_deref(),
            revocation_list.as_deref(),
            policy.as_deref(),
            pinned_key.as_deref(),
        )?;
        println!("{}", serde_json::to_string_pretty(&report)?);
        if report.status != "valid" {
            std::process::exit(1);
        }
        return Ok(());
    }

    enable_raw_mode()?;
    let mut stdout = io::stdout();
    execute!(stdout, EnterAlternateScreen)?;
    let backend = CrosstermBackend::new(stdout);
    let mut terminal = Terminal::new(backend)?;
    let mut app = App::new();
    let result = run_app(&mut terminal, &mut app);
    disable_raw_mode()?;
    execute!(terminal.backend_mut(), LeaveAlternateScreen)?;
    terminal.show_cursor()?;
    result?;
    Ok(())
}

fn run_app<B: ratatui::backend::Backend>(
    terminal: &mut Terminal<B>,
    app: &mut App,
) -> io::Result<()> {
    loop {
        terminal.draw(|frame| draw(frame, app))?;
        if let Event::Key(key) = event::read()? {
            if key.kind != KeyEventKind::Press {
                continue;
            }
            match key.code {
                KeyCode::Char('q') => return Ok(()),
                KeyCode::Tab | KeyCode::Down => {
                    app.selected = (app.selected + 1) % FieldId::all().len();
                }
                KeyCode::BackTab | KeyCode::Up => {
                    app.selected = if app.selected == 0 {
                        FieldId::all().len() - 1
                    } else {
                        app.selected - 1
                    };
                }
                KeyCode::Backspace => {
                    app.value_mut(app.selected_field()).pop();
                }
                KeyCode::Char('v') if key.modifiers.contains(KeyModifiers::CONTROL) => {}
                KeyCode::F(5) => app.run_verify(),
                KeyCode::Enter => app.run_verify(),
                KeyCode::Char(ch) => {
                    app.value_mut(app.selected_field()).push(ch);
                }
                _ => {}
            }
        }
    }
}

fn draw(frame: &mut Frame<'_>, app: &App) {
    let layout = Layout::default()
        .direction(Direction::Vertical)
        .margin(1)
        .constraints([Constraint::Length(11), Constraint::Min(8)])
        .split(frame.area());

    let items = FieldId::all()
        .iter()
        .enumerate()
        .map(|(index, field)| {
            let value = app.value(*field);
            let style = if index == app.selected {
                Style::default()
                    .fg(Color::Yellow)
                    .add_modifier(Modifier::BOLD)
            } else {
                Style::default()
            };
            ListItem::new(Line::from(vec![
                Span::styled(format!("{}: ", field.label()), style),
                Span::raw(value),
            ]))
        })
        .collect::<Vec<_>>();

    let input = List::new(items).block(
        Block::default()
            .title("INK Zero-JS Receipt Verifier")
            .borders(Borders::ALL),
    );
    frame.render_widget(input, layout[0]);

    let result = Paragraph::new(app.result.clone())
        .wrap(Wrap { trim: false })
        .block(
            Block::default()
                .title("Verification Result")
                .borders(Borders::ALL),
        );
    frame.render_widget(result, layout[1]);
}

fn verify_paths(
    receipt: Option<&Path>,
    manifest: Option<&Path>,
    controls: Option<&Path>,
    trust_registry: Option<&Path>,
    revocation_list: Option<&Path>,
    policy: Option<&Path>,
    pinned_key: Option<&str>,
) -> Result<ink_receipt_v2::VerificationReportJson, ink_receipt_v2::ReceiptV2Error> {
    let receipt =
        receipt.ok_or_else(|| ink_receipt_v2::ReceiptV2Error::InvalidInput("receipt path is required".to_string()))?;
    let manifest_bytes = read_optional_path(manifest)?;
    let controls_bytes = read_optional_path(controls)?;
    let trust_registry_bytes = read_optional_path(trust_registry)?;
    let revocation_list_bytes = read_optional_path(revocation_list)?;
    let policy_bytes = read_optional_path(policy)?;
    ink_receipt_v2::verify_receipt(
        &std::fs::read(receipt).map_err(io_error)?,
        manifest_bytes.as_deref(),
        controls_bytes.as_deref(),
        trust_registry_bytes.as_deref(),
        revocation_list_bytes.as_deref(),
        policy_bytes.as_deref(),
        pinned_key,
    )
}

fn read_optional_path(path: Option<&Path>) -> Result<Option<Vec<u8>>, ink_receipt_v2::ReceiptV2Error> {
    path.map(std::fs::read)
        .transpose()
        .map_err(io_error)
}

fn path_or_none(value: &str) -> Option<&Path> {
    (!value.trim().is_empty()).then(|| Path::new(value.trim()))
}

fn string_or_none(value: &str) -> Option<&str> {
    let trimmed = value.trim();
    (!trimmed.is_empty()).then_some(trimmed)
}

fn io_error(error: impl std::fmt::Display) -> ink_receipt_v2::ReceiptV2Error {
    ink_receipt_v2::ReceiptV2Error::InvalidInput(error.to_string())
}

#[cfg(test)]
mod tests {
    use super::verify_paths;
    use serde::Deserialize;
    use serde_json::Value;
    use std::path::Path;
    use std::time::{SystemTime, UNIX_EPOCH};

    #[derive(Debug, Deserialize)]
    struct VectorFile {
        vectors: Vec<SharedVector>,
    }

    #[derive(Debug, Deserialize)]
    struct SharedVector {
        receipt: Value,
        manifest: Option<Value>,
        trust_registry: Option<Value>,
        verify_policy: Option<Value>,
        pinned_public_key: Option<String>,
        expect_status: String,
    }

    #[test]
    fn shared_vector_drives_direct_verify_path() {
        let root = Path::new(env!("CARGO_MANIFEST_DIR"))
            .join("../../../test-vectors/ink-vectors.json");
        let vectors: VectorFile = serde_json::from_slice(&std::fs::read(root).unwrap()).unwrap();
        let vector = &vectors.vectors[0];
        let dir = std::env::temp_dir().join(format!(
            "ink-tui-vector-{}",
            SystemTime::now()
                .duration_since(UNIX_EPOCH)
                .unwrap()
                .as_nanos()
        ));
        std::fs::create_dir_all(&dir).unwrap();
        let receipt_path = dir.join("ink_receipt.v2.json");
        std::fs::write(
            &receipt_path,
            serde_json::to_vec_pretty(&vector.receipt).unwrap(),
        )
        .unwrap();
        let manifest_path = vector.manifest.as_ref().map(|manifest| {
            let path = dir.join("ink_manifest.v2.json");
            std::fs::write(&path, serde_json::to_vec_pretty(manifest).unwrap()).unwrap();
            path
        });
        let trust_path = vector.trust_registry.as_ref().map(|registry| {
            let path = dir.join("trust-registry.json");
            std::fs::write(&path, serde_json::to_vec_pretty(registry).unwrap()).unwrap();
            path
        });
        let policy_path = vector.verify_policy.as_ref().map(|policy| {
            let path = dir.join("verify-policy.json");
            std::fs::write(&path, serde_json::to_vec_pretty(policy).unwrap()).unwrap();
            path
        });
        let report = verify_paths(
            Some(receipt_path.as_path()),
            manifest_path.as_deref(),
            None,
            trust_path.as_deref(),
            None,
            policy_path.as_deref(),
            vector.pinned_public_key.as_deref(),
        )
        .unwrap();
        assert_eq!(report.status, vector.expect_status);
        let _ = std::fs::remove_dir_all(&dir);
    }
}
