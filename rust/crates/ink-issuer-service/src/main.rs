use std::env;
use std::net::SocketAddr;

use axum::extract::State;
use axum::http::StatusCode;
use axum::routing::{get, post};
use axum::{serve, Json, Router};
use ink_host::{issue_hosted_receipt, HostedReceiptIssueRequest};
use serde_json::{json, Value};
use tokio::net::TcpListener;

#[derive(Clone)]
struct AppState;

#[tokio::main]
async fn main() -> Result<(), Box<dyn std::error::Error>> {
    let addr: SocketAddr = env::var("INK_ISSUER_BIND")
        .unwrap_or_else(|_| "127.0.0.1:8787".to_string())
        .parse()?;
    let app = Router::new()
        .route("/up", get(health))
        .route("/v1/receipts/issue", post(issue_receipt))
        .with_state(AppState);
    let listener = TcpListener::bind(addr).await?;
    serve(listener, app).await?;
    Ok(())
}

async fn health() -> Json<Value> {
    Json(json!({ "status": "ok" }))
}

async fn issue_receipt(
    State(_state): State<AppState>,
    Json(request): Json<HostedReceiptIssueRequest>,
) -> Result<Json<Value>, (StatusCode, Json<Value>)> {
    let response = issue_hosted_receipt(&request).map_err(|error| {
        (
            StatusCode::UNPROCESSABLE_ENTITY,
            Json(json!({
                "error": error.to_string(),
            })),
        )
    })?;
    Ok(Json(serde_json::to_value(response).map_err(|error| {
        (
            StatusCode::INTERNAL_SERVER_ERROR,
            Json(json!({
                "error": error.to_string(),
            })),
        )
    })?))
}
