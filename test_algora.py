import unittest

from algora import Algora, Benchmark, Constraints, Weights


class AlgoraTests(unittest.TestCase):
    def setUp(self):
        self.a = Algora()
        self.a.register("fast", lambda x: x + 1, Benchmark(10, 40, .90, .20), tags=["cpu"])
        self.a.register("accurate", lambda x: x * 2, Benchmark(40, 80, .99, .50), tags=["cpu", "quality"])
        self.a.register("cheap", lambda x: x - 1, Benchmark(30, 20, .92, .05), tags=["cpu"])

    def test_names_are_deterministic(self):
        self.assertEqual(self.a.names(), ["accurate", "cheap", "fast"])

    def test_constraints_filter_candidates(self):
        rows = self.a.eligible(Constraints(max_latency_ms=20))
        self.assertEqual([x.name for x in rows], ["fast"])

    def test_required_tags(self):
        rows = self.a.eligible(required_tags=["quality"])
        self.assertEqual([x.name for x in rows], ["accurate"])

    def test_accuracy_weight_selects_accurate(self):
        chosen = self.a.select(weights=Weights(latency=0, memory=0, accuracy=10, cost=0))
        self.assertEqual(chosen.name, "accurate")

    def test_cost_weight_selects_cheap(self):
        chosen = self.a.select(weights=Weights(latency=0, memory=0, accuracy=0, cost=10))
        self.assertEqual(chosen.name, "cheap")

    def test_execute_uses_selected_algorithm(self):
        result = self.a.execute(3, weights=Weights(latency=10, memory=0, accuracy=0, cost=0))
        self.assertEqual(result["algorithm"], "fast")
        self.assertEqual(result["result"], 4)

    def test_evidence_hash_is_order_independent(self):
        other = Algora()
        other.register("cheap", lambda x: x, Benchmark(30, 20, .92, .05), tags=["cpu"])
        other.register("fast", lambda x: x, Benchmark(10, 40, .90, .20), tags=["cpu"])
        other.register("accurate", lambda x: x, Benchmark(40, 80, .99, .50), tags=["quality", "cpu"])
        self.assertEqual(self.a.evidence_hash(), other.evidence_hash())

    def test_no_eligible_candidate_raises(self):
        with self.assertRaises(LookupError):
            self.a.select(Constraints(max_latency_ms=1))

    def test_invalid_metrics_rejected(self):
        with self.assertRaises(ValueError):
            Benchmark(-1, 1)


if __name__ == "__main__":
    unittest.main()
