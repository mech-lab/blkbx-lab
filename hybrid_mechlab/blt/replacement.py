"""Experimental replacement-model scaffolding outside the BLKBX release surface."""


class ReplacementModel:
    def forward_with_replacement(self, batch, replacement_policy):
        _ = (batch, replacement_policy)
        raise NotImplementedError("ReplacementModel is an experimental research placeholder.")
