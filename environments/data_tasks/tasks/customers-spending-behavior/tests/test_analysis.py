import os
import sys
import unittest

import nbformat
import pandas as pd
import numpy as np
import matplotlib
import matplotlib.pyplot as plt
matplotlib.use("Agg")


class GroundTruth:
    def __init__(self, data_path):
        self.df = pd.read_csv(data_path)
        self.df_processed = self._process_features()

    def _process_features(self):
        df = self.df.copy()
        mapping = {
            "Weekly": 52,
            "Bi-Weekly": 26,
            "Fortnightly": 26,
            "Monthly": 12,
            "Quarterly": 4,
            "Annually": 1,
        }
        freq_weights = df["Frequency of Purchases"].map(mapping).fillna(1)
        df["Annual_Value"] = df["Purchase Amount (USD)"] * freq_weights
        return df

    def get_scatter_data(self):
        subset = self.df_processed[self.df_processed["Previous Purchases"] > 10]
        # Set of (Age, Annual_Value)
        return set(zip(subset["Age"], subset["Annual_Value"].round(2)))

    def get_bubble_data(self):
        stats = self.df_processed.groupby("Category").agg(
            x=("Review Rating", "mean"), y=("Purchase Amount (USD)", "sum")
        )
        return {
            cat: (round(row["x"], 4), round(row["y"], 2))
            for cat, row in stats.iterrows()
        }

    def get_avg_revenue_benchmark(self):
        cat_revenues = self.df_processed.groupby("Category")[
            "Purchase Amount (USD)"
        ].sum()
        return round(cat_revenues.mean(), 2)


class NotebookInspector:
    def __init__(self, notebook_path):
        self.notebook_path = notebook_path
        self.captured_figures = []

    def execute(self):
        if not os.path.exists(self.notebook_path):
            print(f"Notebook not found at {self.notebook_path}")
            return

        with open(self.notebook_path) as f:
            nb = nbformat.read(f, as_version=4)

        code_cells = []
        for cell in nb.cells:
            if cell.cell_type == "code":
                lines = [
                    line
                    for line in cell.source.split("\n")
                    if not line.strip().startswith(("!", "%", "pip"))
                ]
                code_cells.append("\n".join(lines))

        full_code = "\n".join(code_cells)

        # Mock plt.show to capture figure
        global_ctx = {"plt": plt, "pd": pd, "np": np, "sns": sys.modules.get("seaborn")}

        def mock_show():
            if plt.get_fignums():
                self.captured_figures.append(plt.gcf())
            plt.figure()

        global_ctx["show"] = mock_show

        try:
            original_show = plt.show
            plt.show = mock_show
            exec(full_code, global_ctx)
        except Exception as e:
            print(f"Runtime Error in Notebook: {e}")
        finally:
            plt.show = original_show

        for i in plt.get_fignums():
            fig = plt.figure(i)
            if fig not in self.captured_figures:
                self.captured_figures.append(fig)


class TestDeepDive(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # 1. Setup ground truth
        cls.truth = GroundTruth("/repo/data/customer_spending.csv")
        # 2. Inspect target notebook
        cls.inspector = NotebookInspector("/repo/analysis.ipynb")
        cls.inspector.execute()
        cls.figs = cls.inspector.captured_figures

    def test_00_sanity(self):
        self.assertGreaterEqual(len(self.figs), 3, "Expected 3 plots, found fewer.")

    # Plot 1: Scatter
    def test_01_scatter_accuracy(self):
        if not self.figs:
            self.fail("No plots found")
        ax = self.figs[0].gca()
        oracle_pts = self.truth.get_scatter_data()

        agent_pts = set()
        for c in ax.collections:
            for x, y in c.get_offsets():
                agent_pts.add((x, round(y, 2)))

        intersection = oracle_pts.intersection(agent_pts)
        if len(oracle_pts) == 0:
            self.fail("Oracle has no data")
        self.assertGreater(
            len(intersection) / len(oracle_pts), 0.95, "Scatter data mismatch"
        )

    def test_02_scatter_style(self):
        ax = self.figs[0].gca()
        self.assertIsNotNone(ax.get_legend(), "Legend missing in Plot 1")
        # Check color diversity
        colors = []
        for c in ax.collections:
            colors.extend(c.get_facecolors())
        if len(colors) > 0:
            unique = len(np.unique(colors, axis=0))
            self.assertGreater(
                unique,
                1,
                "Scatter points are all same color (Subscription mapping missing)",
            )

    # Plot 2: Bubble
    def test_03_bubble_accuracy(self):
        if len(self.figs) < 2:
            self.fail("Plot 2 missing")
        ax = self.figs[1].gca()
        oracle_data = self.truth.get_bubble_data()

        agent_coords = set()
        for c in ax.collections:
            for x, y in c.get_offsets():
                agent_coords.add((round(x, 4), round(y, 2)))

        for cat, (tx, ty) in oracle_data.items():
            if (tx, ty) not in agent_coords:
                self.fail(f"Category '{cat}' missing from Bubble Chart at {tx},{ty}")

    def test_04_bubble_line(self):
        ax = self.figs[1].gca()
        bench = self.truth.get_avg_revenue_benchmark()
        has_line = False
        for line in ax.lines:
            ys = line.get_ydata()
            if (
                len(ys) > 0
                and np.allclose(ys, ys[0])
                and np.isclose(ys[0], bench, rtol=0.01)
            ):
                if line.get_linestyle() in ["--", "dashed"]:
                    has_line = True
        self.assertTrue(has_line, "Missing dashed benchmark line")

    # Plot 3: Heatmap
    def test_05_heatmap_annot(self):
        if len(self.figs) < 3:
            self.fail("Plot 3 missing")
        ax = self.figs[2].gca()
        texts = [
            t.get_text()
            for t in ax.texts
            if t.get_text().replace(".", "", 1).replace("-", "", 1).isdigit()
        ]
        self.assertGreater(len(texts), 5, "Heatmap annotations missing")


if __name__ == "__main__":
    unittest.main()
