use crate::controls::{ControlSet, ControlStatus, ControlType};
use crate::error::Error;
use crate::limits::{
    MAX_CONDITION_NODES, MAX_POLICY_ID_LEN, MAX_POLICY_VERSION_LEN, MAX_REASONS,
    MAX_REASON_CODE_LEN, MAX_RULES,
};
use crate::model_waist::{ModelClass, ReplayStrength, RuntimeKind};
use crate::types::{BoundedBytes, Sha256Digest};

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub enum Decision {
    Pass,
    Warn,
    Escalate,
    Block,
}

impl Decision {
    pub fn as_u8(self) -> u8 {
        match self {
            Decision::Pass => 1,
            Decision::Warn => 2,
            Decision::Escalate => 3,
            Decision::Block => 4,
        }
    }
}

#[derive(Clone, Copy, Debug, Eq, PartialEq, Ord, PartialOrd)]
pub enum RiskClass {
    Low,
    Medium,
    High,
}

#[derive(Clone, Copy, Debug, Eq, PartialEq, Ord, PartialOrd)]
pub enum PluginTrustFact {
    Untrusted,
    LocallyAllowed,
    FirstPartyReference,
    ThirdPartyTrusted,
    ReproduciblyBuilt,
}

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub struct PolicyFacts {
    pub risk_class: RiskClass,
    pub requires_human_review: bool,
    pub binding_effect_present: bool,
    pub provider_fallbacks_allowed: bool,
    pub plugin_trust_level: PluginTrustFact,
    pub runtime_kind: RuntimeKind,
    pub replay_strength: ReplayStrength,
    pub model_class: ModelClass,
}

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub struct RuleEffect<'a> {
    pub decision: Decision,
    pub reason: BoundedBytes<'a, MAX_REASON_CODE_LEN>,
}

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub struct CompiledRule<'a> {
    pub rule_id_hash: Sha256Digest,
    pub priority: u16,
    pub root: u16,
    pub effect: RuleEffect<'a>,
}

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub enum ConditionOp {
    Always,
    RiskClassEquals,
    RiskClassAtLeast,
    RequiresHumanReview,
    BindingEffectPresent,
    ProviderFallbacksAllowed,
    RuntimeKindEquals,
    ReplayStrengthAtLeast,
    ModelClassEquals,
    PluginTrustLevelEquals,
    PluginTrustLevelAtMost,
    ControlPresent,
    ControlApproved,
    And,
    Or,
    Not,
}

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub enum ConditionValue {
    None,
    RiskClass(RiskClass),
    Bool(bool),
    RuntimeKind(RuntimeKind),
    ReplayStrength(ReplayStrength),
    ModelClass(ModelClass),
    PluginTrust(PluginTrustFact),
    ControlType(ControlType),
}

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub struct ConditionNode {
    pub op: ConditionOp,
    pub left: u16,
    pub right: u16,
    pub value: ConditionValue,
}

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub struct CompiledPolicy<'a> {
    pub policy_id: BoundedBytes<'a, MAX_POLICY_ID_LEN>,
    pub policy_version: BoundedBytes<'a, MAX_POLICY_VERSION_LEN>,
    pub policy_hash: Sha256Digest,
    pub nodes: &'a [ConditionNode],
    pub rules: &'a [CompiledRule<'a>],
    pub default_effect: RuleEffect<'a>,
}

impl<'a> CompiledPolicy<'a> {
    pub fn validate(&self) -> Result<(), Error> {
        if self.nodes.len() > MAX_CONDITION_NODES {
            return Err(Error::TooManyConditionNodes);
        }
        if self.rules.len() > MAX_RULES {
            return Err(Error::TooManyRules);
        }
        for rule in self.rules {
            if rule.root as usize >= self.nodes.len() {
                return Err(Error::InvalidRuleRoot);
            }
        }
        for (index, node) in self.nodes.iter().enumerate() {
            validate_node_shape(node, index, self.nodes.len())?;
        }
        validate_node_cycles(self.nodes)?;
        Ok(())
    }
}

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub struct PolicyInput<'a> {
    pub facts: PolicyFacts,
    pub controls: ControlSet<'a>,
}

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub struct ReasonCodeSlot<'a> {
    pub bytes: &'a [u8],
}

pub struct ReasonWriter<'a> {
    pub buf: &'a mut [ReasonCodeSlot<'a>],
    pub len: usize,
}

impl<'a> ReasonWriter<'a> {
    pub fn push(&mut self, reason: crate::types::ReasonCode<'a>) -> Result<(), Error> {
        if self.len >= self.buf.len() || self.len >= MAX_REASONS {
            return Err(Error::TooManyReasons);
        }
        self.buf[self.len] = ReasonCodeSlot {
            bytes: reason.as_bytes(),
        };
        self.len += 1;
        Ok(())
    }

    pub fn as_slice(&self) -> &[ReasonCodeSlot<'a>] {
        &self.buf[..self.len]
    }
}

pub struct EvaluationOut<'a> {
    pub decision: Decision,
    pub reasons: ReasonWriter<'a>,
}

fn has_control(input: &PolicyInput<'_>, control_type: ControlType) -> bool {
    input
        .controls
        .as_slice()
        .iter()
        .any(|obs| obs.control_type == control_type)
}

fn has_approved_control(input: &PolicyInput<'_>, control_type: ControlType) -> bool {
    input.controls.as_slice().iter().any(|obs| {
        obs.control_type == control_type
            && matches!(obs.status, ControlStatus::Approved | ControlStatus::Present)
    })
}

fn bool_leaf_value(value: ConditionValue) -> Result<bool, Error> {
    match value {
        ConditionValue::None => Ok(true),
        ConditionValue::Bool(expected) => Ok(expected),
        _ => Err(Error::InvalidConditionShape),
    }
}

fn eval_node(
    policy: &CompiledPolicy<'_>,
    input: &PolicyInput<'_>,
    index: u16,
) -> Result<bool, Error> {
    let node = policy
        .nodes
        .get(index as usize)
        .ok_or(Error::InvalidConditionIndex)?;
    let value = match node.op {
        ConditionOp::Always => true,
        ConditionOp::RiskClassEquals => {
            matches!(node.value, ConditionValue::RiskClass(v) if v == input.facts.risk_class)
        }
        ConditionOp::RiskClassAtLeast => {
            matches!(node.value, ConditionValue::RiskClass(v) if input.facts.risk_class >= v)
        }
        ConditionOp::RequiresHumanReview => {
            input.facts.requires_human_review == bool_leaf_value(node.value)?
        }
        ConditionOp::BindingEffectPresent => {
            input.facts.binding_effect_present == bool_leaf_value(node.value)?
        }
        ConditionOp::ProviderFallbacksAllowed => {
            input.facts.provider_fallbacks_allowed == bool_leaf_value(node.value)?
        }
        ConditionOp::RuntimeKindEquals => {
            matches!(node.value, ConditionValue::RuntimeKind(v) if v == input.facts.runtime_kind)
        }
        ConditionOp::ReplayStrengthAtLeast => {
            matches!(node.value, ConditionValue::ReplayStrength(v) if input.facts.replay_strength <= v)
        }
        ConditionOp::ModelClassEquals => {
            matches!(node.value, ConditionValue::ModelClass(v) if v == input.facts.model_class)
        }
        ConditionOp::PluginTrustLevelEquals => {
            matches!(node.value, ConditionValue::PluginTrust(v) if v == input.facts.plugin_trust_level)
        }
        ConditionOp::PluginTrustLevelAtMost => {
            matches!(node.value, ConditionValue::PluginTrust(v) if input.facts.plugin_trust_level <= v)
        }
        ConditionOp::ControlPresent => {
            matches!(node.value, ConditionValue::ControlType(v) if has_control(input, v))
        }
        ConditionOp::ControlApproved => {
            matches!(node.value, ConditionValue::ControlType(v) if has_approved_control(input, v))
        }
        ConditionOp::And => {
            eval_node(policy, input, node.left)? && eval_node(policy, input, node.right)?
        }
        ConditionOp::Or => {
            eval_node(policy, input, node.left)? || eval_node(policy, input, node.right)?
        }
        ConditionOp::Not => !eval_node(policy, input, node.left)?,
    };
    Ok(value)
}

pub fn evaluate_policy<'a>(
    input: PolicyInput<'a>,
    policy: CompiledPolicy<'a>,
    out: &mut EvaluationOut<'a>,
) -> Result<(), Error> {
    input.controls.validate()?;
    policy.validate()?;
    out.decision = policy.default_effect.decision;
    out.reasons.len = 0;
    out.reasons.push(policy.default_effect.reason)?;
    for rule in policy.rules {
        if eval_node(&policy, &input, rule.root)? {
            out.decision = rule.effect.decision;
            out.reasons.len = 0;
            out.reasons.push(rule.effect.reason)?;
            return Ok(());
        }
    }
    Ok(())
}

fn validate_node_shape(node: &ConditionNode, index: usize, node_count: usize) -> Result<(), Error> {
    let child_valid = |child: u16| (child as usize) < node_count;
    match node.op {
        ConditionOp::Always => {
            if !matches!(node.value, ConditionValue::None) || node.left != 0 || node.right != 0 {
                return Err(Error::InvalidConditionShape);
            }
        }
        ConditionOp::RiskClassEquals | ConditionOp::RiskClassAtLeast => {
            if !matches!(node.value, ConditionValue::RiskClass(_))
                || node.left != 0
                || node.right != 0
            {
                return Err(Error::InvalidConditionShape);
            }
        }
        ConditionOp::RequiresHumanReview
        | ConditionOp::BindingEffectPresent
        | ConditionOp::ProviderFallbacksAllowed => {
            if !matches!(node.value, ConditionValue::None | ConditionValue::Bool(_))
                || node.left != 0
                || node.right != 0
            {
                return Err(Error::InvalidConditionShape);
            }
        }
        ConditionOp::RuntimeKindEquals => {
            if !matches!(node.value, ConditionValue::RuntimeKind(_))
                || node.left != 0
                || node.right != 0
            {
                return Err(Error::InvalidConditionShape);
            }
        }
        ConditionOp::ReplayStrengthAtLeast => {
            if !matches!(node.value, ConditionValue::ReplayStrength(_))
                || node.left != 0
                || node.right != 0
            {
                return Err(Error::InvalidConditionShape);
            }
        }
        ConditionOp::ModelClassEquals => {
            if !matches!(node.value, ConditionValue::ModelClass(_))
                || node.left != 0
                || node.right != 0
            {
                return Err(Error::InvalidConditionShape);
            }
        }
        ConditionOp::PluginTrustLevelEquals | ConditionOp::PluginTrustLevelAtMost => {
            if !matches!(node.value, ConditionValue::PluginTrust(_))
                || node.left != 0
                || node.right != 0
            {
                return Err(Error::InvalidConditionShape);
            }
        }
        ConditionOp::ControlPresent | ConditionOp::ControlApproved => {
            if !matches!(node.value, ConditionValue::ControlType(_))
                || node.left != 0
                || node.right != 0
            {
                return Err(Error::InvalidConditionShape);
            }
        }
        ConditionOp::And | ConditionOp::Or => {
            if !matches!(node.value, ConditionValue::None)
                || !child_valid(node.left)
                || !child_valid(node.right)
                || node.left as usize == index
                || node.right as usize == index
            {
                return Err(Error::InvalidConditionShape);
            }
        }
        ConditionOp::Not => {
            if !matches!(node.value, ConditionValue::None)
                || !child_valid(node.left)
                || node.right != 0
                || node.left as usize == index
            {
                return Err(Error::InvalidConditionShape);
            }
        }
    }
    Ok(())
}

fn validate_node_cycles(nodes: &[ConditionNode]) -> Result<(), Error> {
    let mut states = [0u8; MAX_CONDITION_NODES];
    for index in 0..nodes.len() {
        validate_node_acyclic(nodes, index, &mut states)?;
    }
    Ok(())
}

fn validate_node_acyclic(
    nodes: &[ConditionNode],
    index: usize,
    states: &mut [u8; MAX_CONDITION_NODES],
) -> Result<(), Error> {
    match states[index] {
        1 => return Err(Error::InvalidConditionCycle),
        2 => return Ok(()),
        _ => {}
    }

    states[index] = 1;
    let node = &nodes[index];
    match node.op {
        ConditionOp::And | ConditionOp::Or => {
            validate_node_acyclic(nodes, node.left as usize, states)?;
            validate_node_acyclic(nodes, node.right as usize, states)?;
        }
        ConditionOp::Not => {
            validate_node_acyclic(nodes, node.left as usize, states)?;
        }
        _ => {}
    }
    states[index] = 2;
    Ok(())
}
