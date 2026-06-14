import pytest
from fre_core.build_proofgraph import build_proofgraph, build_proofgraph_prompt
from fre_core.schemas import ReadinessDimension, ReadinessReport, TheoremProofUnit
from fre_core.validation import ArtifactValidationError

class Fake:
    def extract_json(self, *, prompt, schema):
        return schema(unit_id="u", nodes=[{"node_id":"N1","node_type":"stmt","text":"t"},{"node_id":"N2","node_type":"lib","text":"SimpleGraph.IsTree.card_edgeFinset"}], edges=[{"source":"N1","target":"N2","edge_type":"aligns_with_library_candidate"}])
class Bad:
    def extract_json(self, *, prompt, schema):
        return schema(unit_id="u", nodes=[{"node_id":"N1","node_type":"s","text":"t"}], edges=[{"source":"N1","target":"N1","edge_type":"bad"}])

def test_prompt():
    u = TheoremProofUnit(unit_id="u", source_id="s", statement="tree", proof="p", domain="graph_theory")
    r = ReadinessReport(unit_id="u", statement_readiness=ReadinessDimension(status="clear", recovered=[], unresolved=[]), context_readiness=ReadinessDimension(status="partial", recovered=[], unresolved=[]), notation_readiness=ReadinessDimension(status="partial", recovered=[], unresolved=[]), dependency_readiness=ReadinessDimension(status="partial", recovered=[], unresolved=[]), existing_theorem_candidates=["SimpleGraph.IsTree.card_edgeFinset"], constructive_path=["leaf"], blockers=["b"], recommended_next_action="go")
    assert "SimpleGraph.IsTree.card_edgeFinset" in build_proofgraph_prompt(u, r)

def test_build():
    u = TheoremProofUnit(unit_id="u", source_id="s", statement="tree", proof="p", domain="graph_theory")
    assert build_proofgraph(unit=u, model_client=Fake()).unit_id == "u"

def test_bad_edge():
    u = TheoremProofUnit(unit_id="u", source_id="s", statement="tree", proof="p", domain="graph_theory")
    with pytest.raises(ArtifactValidationError):
        build_proofgraph(unit=u, model_client=Bad())
