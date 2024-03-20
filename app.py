from functools import partial
import logging
import ipywidgets as wd
import polars as pl
from IPython.display import display, HTML, clear_output
import bokeh.plotting as bp
import streamlit as st
from bokeh.plotting import figure, show
from bokeh.io import output_notebook
from bokeh.layouts import column
from bokeh.models import (
    ranges,
    LinearAxis,
    HoverTool,
    CrosshairTool,
    Slider,
    CustomJS,
    Span,
    ColumnDataSource
)
from PIL import Image
from src.power_curve import get_power_at_wind_velocity, read_power_curve
from src.turbines import TURBINES
from src.impingement import calculate_impingement
import matplotlib.pyplot as plt
from streamlit_folium import st_folium
import math
from src.map import generate_map

output_notebook()


class App:
    price_data: pl.LazyFrame
    weather_data: pl.LazyFrame
    _combined_data: pl.LazyFrame
    logger = logging.getLogger("App")
    logger.setLevel(logging.INFO)

    def __init__(self):
        self.plot_outputs = wd.Output()
        self.impingement_plot_output = wd.Output()
        grid = wd.GridspecLayout(1, 2)
        turbine_params = wd.Output()
        power_curves = wd.Output()
        grid[0, 0] = wd.VBox(
            (
                wd.Label("Wind Turbine"),
                (
                    turbine_dropdown := wd.Dropdown(
                        description="Select wind turbine: ",
                        options=tuple(TURBINES.keys()),
                        value=None,
                        style={"description_width": "initial"},
                    )
                ),
                turbine_params,
                power_curves,
                self.impingement_plot_output,
            )
        )

        turbine_dropdown.observe(
            partial(self._set_turbine_params, output=turbine_params), names="value"
        )
        turbine_dropdown.observe(
            partial(self._show_power_curves, output=power_curves), names="value"
        )

        grid[0, 1] = wd.VBox((self.plot_outputs,))

        self.grid = grid

    @staticmethod
    def _set_turbine_params(change: dict, output: wd.Output):
        turbine_name = change["new"]
        turbine_params = TURBINES[turbine_name]

        stats = []
        for key, value in turbine_params.items():
            if key == "power_curve":
                continue
            stats.append(
                wd.HBox(
                    (
                        wd.Label(f"{key}:", layout={"width": "150px"}),
                        wd.Label(f"{value}"),
                    )
                )
            )

        box = wd.VBox(stats)

        with output:
            clear_output(wait=True)
            display(box)

    def _read_impingement_data(self, selected_turbine, selected_windfarm):
        (
            impingement_raw,
            impingement_testdata,
            r_acc_limit,
            lossvector,
        ) = calculate_impingement(
            turbine=TURBINES[selected_turbine], windfarm=selected_windfarm, slider=1
        )
        source = ColumnDataSource(data={
            'timestamp': impingement_raw["timestamp"],
            'lossvector': lossvector
        })

        p = figure(title="Turbine Efficiency Over Time",
                x_axis_label='Timestamp',
                y_axis_label='Turbine Efficiency [%]',
                x_axis_type='datetime',
                plot_width=600,
                plot_height=300)

        p.line(x='timestamp', y='lossvector', source=source)
        st.bokeh_chart(p, use_container_width=True)

    def read_price_data(self, path: str):
        """Read the price history."""
        # Country,ISO3 Code,Datetime (UTC),Datetime (Local),Price (EUR/MWhe)
        schema = {
            "Country": pl.Categorical,
            "ISO3 Code": pl.Categorical,
            "Datetime (UTC)": pl.Datetime("ms"),
            "Datetime (Local)": pl.Datetime("ms"),
            "Price (EUR/MWhe)": pl.Float32,
        }
        price_data = (
            pl.read_csv(path, schema=schema)
            .lazy()
            .select(
                [
                    pl.col("Datetime (Local)").alias("time"),
                    pl.col("Price (EUR/MWhe)").alias("price"),
                ]
            )
        )
        price_data = price_data.set_sorted(pl.col("time"))
        price_data = price_data.filter(pl.col("time").dt.year() < 2020)
        self.price_data = price_data
        return self.price_data

    @property
    def combined_data(self):
        return self._combined_data.collect()
    
    # def load_data(self, selected_windfarm):
    #     _combined_data = 

    def read_weather_data(self, path: str):
        """Read weather data."""
        schema = {
            "timestamp": pl.Datetime("ms"),
            "rainc": pl.Float32,
            "qrain_120.0": pl.Float32,
            "rho_120.0": pl.Float32,
            "wsp_120.0": pl.Float32,
            "qrain_150.0": pl.Float32,
            "rho_150.0": pl.Float32,
            "wsp_150.0": pl.Float32,
        }
        data = (
            pl.read_csv(path, schema=schema)
            .lazy()
            .select(
                [
                    pl.col("timestamp").alias("time"),
                    pl.col("wsp_150.0").alias("wind_speed"),
                ]
            )
            .set_sorted(pl.col("time"))
        )
        self.weather_data = data
        return self.weather_data

    def _join_data(self, selected_turbine):
        combined_data = self.weather_data.join(self.price_data, on="time", how="inner")
        combined_data = combined_data.with_columns(
            power=pl.col("wind_speed").map_elements(
                lambda value: get_power_at_wind_velocity(value, TURBINES[selected_turbine]["power_curve"]) * 1e-6
            )
        )
        combined_data = combined_data.with_columns(
            income=pl.col("power") * pl.col("price")
        )
        combined_data = combined_data.with_columns(
            income_sma=pl.col("income").rolling_mean(window_size="1mo", by="time"),
            price_sma=pl.col("price").rolling_mean(window_size="1mo", by="time"),
        )
        self._combined_data = combined_data
        return self._combined_data

    def _create_price_plot(self):
        data = self.combined_data
        source = bp.ColumnDataSource(
            data=dict(
                time=data.select(pl.col("time")).to_series(),
                price=data.select(pl.col("price")).to_series(),
                price_sma=data.select(pl.col("price_sma")).to_series(),
            )
        )
        hover_tool = HoverTool(
            tooltips=[
                ("Time", "@time{%F %T}"),
                ("Price", "@price"),
                ("Price (rolling mean)", "@price_sma"),
            ],
            formatters={"@time": "datetime"},
            mode="vline",
        )
        fig = figure(
            title="Electricity price (€/MWh), 1 hour average",
            x_axis_type="datetime",
            y_axis_label="Price (€/MWh)",
            width=600,
            height=300,
            tools=[
                hover_tool,
                CrosshairTool(),
                "pan",
                "wheel_zoom",
                "box_zoom",
                "reset",
                "save",
            ],
        )
        line = fig.line("time", "price", source=source)
        hover_tool.renderers = [line]
        fig.line("time", "price_sma", source=source, color="red", line_width=3)
        st.bokeh_chart(fig, use_container_width=True)

        return fig

    def _create_income_plot(self):
        data = self.combined_data
        source = bp.ColumnDataSource(
            data=dict(
                time=data.select(pl.col("time")).to_series(),
                income=data.select(pl.col("income")).to_series(),
                income_sma=data.select(pl.col("income_sma")).to_series(),
            )
        )
        hover_tool = HoverTool(
            tooltips=[
                ("Time", "@time{%F %T}"),
                ("Income", "@income"),
                ("Income (rolling mean)", "@income_sma"),
            ],
            formatters={"@time": "datetime"},
            mode="vline",
        )
        fig = figure(
            title="Revenue (€), 1 hour average",
            x_axis_type="datetime",
            y_axis_label="Revenue (€)",
            width=600,
            height=300,
            tools=[
                hover_tool,
                CrosshairTool(),
                "pan",
                "wheel_zoom",
                "box_zoom",
                "reset",
                "save",
            ],
        )
        line = fig.line("time", "income", source=source)
        hover_tool.renderers = [line]
        fig.line("time", "income_sma", source=source, color="red", line_width=3)
        st.bokeh_chart(fig, use_container_width=True)

        return fig

    def create_figures(self):
        return column(self._create_price_plot(), self._create_income_plot())

    def refresh_figures(self):
        with self.plot_outputs:
            show(self.create_figures())
        self._read_impingement_data()

    def _create_power_curve_plot(self, selected_turbine):
        turbine_name = selected_turbine
        curve = pl.from_dict(TURBINES[turbine_name]["power_curve"]).lazy()

        curve = (
            curve.filter(pl.col("power") > 0)
            .with_columns(
                tip_speed=pl.col("rotor_speed")
                .mul(math.pi / 30)
                .mul(TURBINES[turbine_name]["radius"])
            )
            .filter(pl.col("tip_speed") > 0)
            .collect()
        )

        source = bp.ColumnDataSource(data=curve.to_dict())

        fig_0 = figure(
            title="Wind speed-Power curve",
            y_axis_label="Power (MW)",
            width=600,
            height=200,
            tools=[
                CrosshairTool(),
                "pan",
                "wheel_zoom",
                "box_zoom",
                "reset",
                "save",
            ],
        )
        fig_0.line("wind_speed", "power", source=source)

        fig_1 = figure(
            title="Wind speed-Rotor speed curve",
            y_axis_label="Rotor speed (1/min)",
            x_axis_label="Wind speed (m/s)",
            width=600,
            height=200,
            tools=[
                CrosshairTool(),
                "pan",
                "wheel_zoom",
                "box_zoom",
                "reset",
                "save",
            ],
        )
        fig_1.line("wind_speed", "rotor_speed", source=source)

        # Create a new ColumnDataSource to hold data for the movable point
        point_source = bp.ColumnDataSource(data=dict(x=[0], y=[0]))

        fig_2 = figure(
            title="Tip speed-Power curve",
            y_axis_label="Tip speed (m/s)",
            x_axis_label="Power (MW)",
            width=600,
            height=200,
            tools=["crosshair", "pan", "wheel_zoom", "box_zoom", "reset", "save"],
        )

        # Draw the curve line
        fig_2.line("power", "tip_speed", source=source)

        # Draw the movable point
        fig_2.circle("x", "y", source=point_source, size=10, color="red")

        # Create the Slider object
        slider = Slider(
            start=min(source.data["tip_speed"]),
            end=max(source.data["tip_speed"]),
            value=min(source.data["tip_speed"]),
            step=1,
            title="Tip speed (m/s)",
        )

        # Initialize a horizontal line (Span) passing through the point
        vertical_line = Span(
            location=point_source.data["y"][0],  # Initial y-value of the point
            dimension="height",
            line_color="red",
            line_width=1,
        )
        self.power_cap = vertical_line

        # Add the horizontal line to the figure
        fig_2.add_layout(vertical_line)

        # JavaScript code to be called whenever the slider moves
        callback = CustomJS(
            args=dict(
                source=source,
                point_source=point_source,
                slider=slider,
                vertical_line=vertical_line,
            ),
            code="""
            const data = source.data;
            const P = data['tip_speed'];
            const T = data['power'];
            const pos = slider.value;
            const point_data = point_source.data;

            // Find index on the curve closest to the slider value
            let index = 0;
            let min_dist = Number.MAX_VALUE;
            for (let i = 0; i < P.length; i++) {
                let dist = Math.abs(P[i] - pos);
                if (dist < min_dist) {
                    min_dist = dist;
                    index = i;
                }
            }

            // Update the point's position to the curve's corresponding y-value 
            point_data['x'][0] = T[index];
            point_data['y'][0] = P[index];
            point_source.change.emit();
            // Update the horizontal line to pass through the new point
            vertical_line.location = point_data['x'][0];
        """,
        )

        # Attach callback to slider
        slider.js_on_change("value", callback)

        layout = column(slider, fig_2)

        return layout
        # return column(fig_2, fig_0, fig_1)
        # return fig_2

    def _show_power_curves(self, selected_turbine):
        figures = self._create_power_curve_plot(selected_turbine)
        st.bokeh_chart(figures, use_container_width=True)

    def _generate_map(self, selected_location):
        # mapping = {
        #     "Latvia": "e2",
        #     "Denmark": "nordsen iii vest"
        # }
        # ofwfarm_map = generate_map(mapping[selected_location])
        ofwfarm_map = generate_map(selected_location)
        with st.sidebar.container():
            st_folium(ofwfarm_map, height=300, use_container_width=True)
        # st.sidebar.add_rows(st_folium(ofwfarm_map, width=7000, height=350))
        # st_folium(ofwfarm_map, use_container_width=True)

    def _write_turbine_properties(self, selected_turbine):
        # st.sidebar.divider()
        st.sidebar.write(f"Cut in wind speed: {TURBINES[selected_turbine]['cut_in_wind_speed']}")
        # st.sidebar.divider()
        st.sidebar.write(f"Cut out wind speed:{TURBINES[selected_turbine]['cut_out_wind_speed']}")
        # st.sidebar.divider()
        st.sidebar.write(f"Radius: {TURBINES[selected_turbine]['radius']}")
        # st.sidebar.divider()

    def main(self):
        # st.title("Wind Turbine Analysis")
        st.sidebar.image("./data/logos/windfarm_logo.png")
        selected_turbine = st.sidebar.selectbox("Select wind turbine model:", options=list(TURBINES.keys()), index=0)
        self._write_turbine_properties(selected_turbine)
        selected_location = st.sidebar.selectbox("Select wind turbine location:", options=["e2", "nordsen iii vest"], index=0)
        self._generate_map(selected_location)
        st.sidebar.image("./data/logos/ramboll_logo_big.png")
        # selected_location = st.sidebar.selectbox("Select wind turbine location:", options=["Denmark", "Latvia"], index=0)

        map_selection = {
            "e2": "data/price_data/Denmark.csv",
            "nordsen iii vest": "data/price_data/Denmark.csv"
        }

        price_data = self.read_price_data(map_selection[selected_location])
        weather_data = self.read_weather_data("data/weather_data.csv")
        combined_data = self._join_data(selected_turbine)

        box11, box12 = st.columns(2)
        with box11:
            st.header("Wind Turbine Statistics")
            self._show_power_curves(selected_turbine)
            self._read_impingement_data(selected_turbine, selected_location)
        with box12:
            st.header("Market Price")
            self._create_price_plot()
            self._create_income_plot()
        # box21, box22 = st.columns(2)
        # with box21:
        #     st.header("Impingement")
        # with box22:
        #     st.header("Previous Something")
        #     self._create_price_plot()
        #     self._create_income_plot()


if __name__ == "__main__":
    st.set_page_config(
        page_title="Wind Turbine Analysis",
        layout="wide",
        page_icon="./data/logos/ramboll_logo.ico"
    )
    app = App()
    app.main()
