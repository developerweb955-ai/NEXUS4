import pandas as pd

from engines.data_loader import NexusDataLoader
from engines.data_inspector import NexusDataInspector
from engines.data_cleaner import NexusDataCleaner
from engines.analytics import NexusAnalyticsEngine
from engines.visualization import NexusVisualizationEngine
from engines.report_engine import NexusReportEngine

# ==========================================
# NEXUS - INTEGRATION CONTROLLER
# ==========================================

class NexusIntegrationController:

    def __init__(self, report_directory="nexus_reports"):

        self.loader = NexusDataLoader()

        self.inspector = None
        self.cleaner = None
        self.analytics = None
        self.visualizer = None
        self.report_engine = NexusReportEngine(
            output_directory=report_directory
        )

        self.dataset = None
        self.cleaned_dataset = None
        self.profile = None
        self.insights = None
        self.charts = {}

    def load_dataset(self, file_path):

        self.dataset = self.loader.load(file_path)

        self.cleaned_dataset = None
        self.inspector = None
        self.cleaner = None
        self.analytics = None
        self.visualizer = None
        self.profile = None
        self.insights = None
        self.charts = {}

        return self.dataset

    def inspect_dataset(self):

        if self.dataset is None:
            raise RuntimeError(
                "Load a dataset before inspection."
            )

        inspection_data = (
            self.cleaned_dataset
            if self.cleaned_dataset is not None
            else self.dataset
        )

        self.inspector = NexusDataInspector(
            inspection_data
        )

        self.profile = self.inspector.generate_profile()

        return self.profile

    def clean_dataset(self, operations=None):

        if self.dataset is None:
            raise RuntimeError(
                "Load a dataset before cleaning."
            )

        self.cleaner = NexusDataCleaner(
            self.dataset
        )

        if operations is not None:

            if not isinstance(operations, list):
                raise TypeError(
                    "Operations must be supplied as a list."
                )

            for operation in operations:

                if not isinstance(operation, dict):
                    raise TypeError(
                        "Each cleaning operation must be a dictionary."
                    )

                name = operation.get("name")
                parameters = operation.get("parameters", {})

                if not isinstance(parameters, dict):
                    raise TypeError(
                        "Operation parameters must be a dictionary."
                    )

                available_operations = {
                    "remove_duplicates":
                        self.cleaner.remove_duplicates,

                    "handle_missing_values":
                        self.cleaner.handle_missing_values,

                    "convert_data_types":
                        self.cleaner.convert_data_types,

                    "trim_whitespace":
                        self.cleaner.trim_whitespace
                }

                if name not in available_operations:
                    raise ValueError(
                        f"Unsupported cleaning operation: {name}"
                    )

                available_operations[name](**parameters)

        self.cleaned_dataset = (
            self.cleaner.get_cleaned_data()
        )

        # Cleaning changes the active dataset. Invalidate derived artifacts
        # so later analysis, charts, and reports cannot reuse stale results.
        self.profile = None
        self.insights = None
        self.analytics = None
        self.visualizer = None
        self.charts = {}

        return self.cleaned_dataset

    def analyze_dataset(self):

        if self.dataset is None:
            raise RuntimeError(
                "Load a dataset before analysis."
            )

        analysis_data = (
            self.cleaned_dataset
            if self.cleaned_dataset is not None
            else self.dataset
        )

        self.analytics = NexusAnalyticsEngine(
            analysis_data
        )

        self.insights = self.analytics.generate_insights()

        return self.insights

    def create_visualizations(self):

        if self.dataset is None:
            raise RuntimeError(
                "Load a dataset before visualization."
            )

        visualization_data = (
            self.cleaned_dataset
            if self.cleaned_dataset is not None
            else self.dataset
        )

        self.visualizer = NexusVisualizationEngine(
            visualization_data
        )

        self.charts = {}

        numeric_columns = visualization_data.select_dtypes(
            include="number"
        ).columns.tolist()

        categorical_columns = visualization_data.select_dtypes(
            include=["object", "category", "bool", "string"]
        ).columns.tolist()

        if numeric_columns:
            self.charts["histogram"] = (
                self.visualizer.histogram(
                    numeric_columns[0]
                )
            )

        if len(numeric_columns) >= 2:
            self.charts["scatter"] = (
                self.visualizer.scatter_plot(
                    numeric_columns[0],
                    numeric_columns[1]
                )
            )

            self.charts["correlation_heatmap"] = (
                self.visualizer.correlation_heatmap()
            )

        if numeric_columns and categorical_columns:
            self.charts["bar"] = (
                self.visualizer.bar_chart(
                    categorical_columns[0],
                    numeric_columns[0]
                )
            )

            self.charts["box"] = (
                self.visualizer.box_plot(
                    categorical_columns[0],
                    numeric_columns[0]
                )
            )

        if categorical_columns:
            self.charts["pie"] = (
                self.visualizer.pie_chart(
                    categorical_columns[0]
                )
            )

        return self.charts

    def generate_report(self, filename=None):

        if self.dataset is None:
            raise RuntimeError(
                "Load a dataset before generating a report."
            )

        if self.profile is None:
            self.inspect_dataset()

        if self.insights is None:
            self.analyze_dataset()

        report_data = (
            self.cleaned_dataset
            if self.cleaned_dataset is not None
            else self.dataset
        )

        return self.report_engine.generate_report(
            dataframe=report_data,
            profile=self.profile,
            insights=self.insights,
            filename=filename
        )

    def get_pipeline_status(self):

        return {
            "dataset_loaded": self.dataset is not None,
            "dataset_inspected": self.profile is not None,
            "dataset_cleaned": self.cleaned_dataset is not None,
            "dataset_analyzed": self.insights is not None,
            "visualizations_created": bool(self.charts),
            "visualization_count": len(self.charts)
        }


print("NEXUS INTEGRATION CONTROLLER CREATED")
