from hybrid_mechlab.blt.replacement import ReplacementModel


def test_replacement_model_interface():
    rm = ReplacementModel()
    try:
        rm.forward_with_replacement(batch=None, replacement_policy=None)
    except NotImplementedError:
        pass
