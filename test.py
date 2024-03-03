import dash
import dash_html_components as html
from dash.dependencies import Input, Output
from dash import dcc, html
import paho.mqtt.client as mqtt

app = dash.Dash(__name__)

# MQTT configuration
mqtt_broker = "iobrokerpi"
mqtt_topic = "Wohnzimmer/esp_wohnzimmer1/sensor/bme280_temp/state"

# Initial temperature value
initial_temperature = "N/A"

# MQTT callback function
def on_message(client, userdata, msg):
    global initial_temperature
    initial_temperature = msg.payload.decode("utf-8")

# Set up MQTT client
client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
client.on_message = on_message
client.connect(mqtt_broker, 1883, 60)
client.subscribe(mqtt_topic)
client.loop_start()

# Layout of the app
app.layout = html.Div(
    [
        html.H1("Temperature Monitoring App"),
        html.Div(id="temperature-display"),
        dcc.Interval(
            id='interval-component',
            interval=10*1000,  # in milliseconds, update every 10 seconds
            n_intervals=0
        ),
    ]
)

# Callback to update temperature
@app.callback(
    Output("temperature-display", "children"),
    [Input("interval-component", "n_intervals")]
)
def update_temperature(n_intervals):
    global initial_temperature
    return f"Current Temperature: {initial_temperature} °C"

if __name__ == "__main__":
    app.run_server(debug=True)
