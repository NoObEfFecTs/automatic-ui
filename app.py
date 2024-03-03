import dash
import dash_bootstrap_components as dbc
from dash.dependencies import Input, Output, State
from dash import html, dcc, ALL
import json
import paho.mqtt.client as mqtt

app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP, '/assets/styles.css'])

# Load data from JSON file
with open('data.json', 'r', encoding="utf-8") as file:
    data = json.load(file)

store = dcc.Store(data={}, id="data", storage_type='memory')

# MQTT configuration
mqtt_broker = "iobrokerpi"
mqtt_topic = "Wohnzimmer/#"
mqtt_username = "pi"  # Replace with your MQTT broker username
mqtt_password = "raspberry"  # Replace with your MQTT broker password

# MQTT callback function
def on_message(client, userdata, msg):
    global store
    # initial_temperature = msg.payload.decode("utf-8")
    store.data[msg.topic] = msg.payload.decode("utf-8")

# Set up MQTT client with optional username and password
client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
client.username_pw_set(username=mqtt_username, password=mqtt_password)
client.on_message = on_message
client.connect(mqtt_broker, 1883, 60)
client.subscribe(mqtt_topic)
client.loop_start()


# Function to create a DBC Card with dynamic content
def create_card(card_data):
    overlay_info = card_data['overlay_info'][0] if card_data['overlay_info'] else ''
    # info = [dbc.Col(html.P(info, className='card-text'), class_name='card-info-col') for info in card_data["overlay_info"]],
    all_info = []
    for tmp_info in card_data["overlay_info"]:
        if "topic" in tmp_info.keys() and tmp_info["topic"] in store.data.keys():
            if "unit" in tmp_info.keys():
                info_content = store.data[tmp_info["topic"]] + " " + tmp_info["unit"]
            else:
                info_content = store.data[tmp_info["topic"]]
        else:
            if "unit" in tmp_info.keys():
                info_content = tmp_info["content"] + " " +tmp_info["unit"]
            else:    
                info_content = tmp_info["content"]
        all_info.append(dbc.Col([dbc.Col(html.P(tmp_info["title"], className='info-title')), dbc.Col(html.P(info_content, className='info-content'))], class_name='card-info-col'))
    # info = [dbc.Col([dbc.Col(html.P(info["title"], className='info-title')), dbc.Col(html.P(info["content"], className='info-content'))], class_name='card-info-col') for info in card_data["overlay_info"]],
    # info = info[0]
    return dbc.Card(
        [
            dbc.CardImg(src=card_data['background_image'], top=True, class_name="card-img"),
            dbc.CardBody(
                [
                    dbc.Row(html.H4(card_data['title'], className='card-title'), class_name='card-title-row'),
                    dbc.Row(children=all_info, class_name='card-info-row'),
                    # dbc.Row(html.P(overlay_info, className='card-text'), class_name='card-info-row'),  # Display the first element if available
                    dbc.Row(dbc.Button("Open Modal", id={'type': 'button', 'index': f'btn_{card_data["id"]}'}, color='primary', className='mr-2'), class_name='card-button-row'),
                ]
            ),
        ],
        id={'type': 'card', 'index': f'crd_{card_data["id"]}'},
    )


# Function to create a modal with dynamic content
def create_modal(card_id):
    card_data = next(card for card in data['cards'] if card['id'] == int(card_id))

    modal_content = []

    # Buttons
    if 'buttons' in card_data['modal_content']:
        modal_content.extend([dbc.Button(button, color='primary', className='mr-2') for button in card_data['modal_content']['buttons']])

    # Dropdowns
    if 'dropdowns' in card_data['modal_content']:
        modal_content.extend([dbc.DropdownMenu(
            label='Dropdown',
            children=[
                dbc.DropdownMenuItem(option, id=f'dropdown-{card_id}-{i}', n_clicks=0) for i, option in enumerate(dropdown['options'])
            ],
        ) for dropdown in card_data['modal_content']['dropdowns']])

    # Radio Buttons
    if 'radio_buttons' in card_data['modal_content']:
        modal_content.extend([dbc.RadioItems(
            options=[{'label': option, 'value': option} for option in radio['options']],
            value=radio['default'],
            inline=True,
        ) for radio in card_data['modal_content']['radio_buttons']])

    # Sliders
    if 'sliders' in card_data['modal_content']:
        modal_content.extend([dcc.Slider(
            min=slider['min'],
            max=slider['max'],
            step=slider['step'],
            value=slider['default'],
            marks={i: str(i) for i in range(slider['min'], slider['max'] + 1)},
        ) for slider in card_data['modal_content']['sliders']])

    # Iframes
    if 'iframes' in card_data['modal_content']:
        modal_content.extend([html.Iframe(src=iframe, width='100%', height='400px') for iframe in card_data['modal_content']['iframes']])

    modal_size = 'xl'

    tmp_mod = dbc.Modal(
        [
            dbc.ModalHeader(card_data['title'], close_button=False),
            dbc.ModalBody(modal_content),
            dbc.ModalFooter(
                dbc.Button("Close", id={'type': 'close-modal-button', 'index': f'close-modal_{card_id}'}, className="ml-auto", n_clicks=0)
            ),
        ],
        id='modal_' + str(card_data['id']),
        size=modal_size,
        keyboard=False,
        backdrop="static"
    )

    return tmp_mod


def create_layout(data):

    # Layout of the app
    modals = []

    for card in data["cards"]:
        mod = create_modal(card["id"])
        modals.append(mod)
        
    layout = [
        dbc.Row(dbc.Col(html.H1("Smart Home Dashboard")), className="app-title"),
        dbc.Row(
            [dbc.Col(create_card(card)) for card in data['cards']],
        ),
        *modals,
        store,
        # dcc.Interval(
        #     id='interval-component',
        #     interval=5*1e3,  # in milliseconds, update every 10 seconds
        #     n_intervals=0
        # ),
    ]

    return layout
    

app.layout = html.Div(
    create_layout(data),
    id="app-layout"
)


mod_outputs = []
for card in data["cards"]:
    mod_outputs.append(Output("modal_"+str(card["id"]), "is_open"))


# Callback to open the modal on button click and close the modal
@app.callback(
    mod_outputs,
    Input({'type': 'button', 'index': ALL}, 'n_clicks'),
    Input({'type': 'close-modal-button', 'index': ALL}, 'n_clicks'),
    prevent_initial_call=True,
)
def update_modal(n_clicks_button, n_clicks_close):
    ctx = dash.callback_context
    triggered_id = ctx.triggered_id

    res = [False] * len(mod_outputs)

    # print(f"Triggered ID: {triggered_id}")

    if triggered_id and 'index' in triggered_id and not "close" in triggered_id["index"]:
        card_id = int(triggered_id['index'].split("_")[1])
        res[card_id] = True
        # print(f"Button Clicked - Card ID: {card_id}")
        return res

    else:
        # print("Close Button Clicked")
        return res

    return False, None

@app.callback(
    Output("app-layout", "children"),
    Input({'type': 'close-modal-button', 'index': ALL}, 'n_clicks'),
    State("data", "data"),
)

def update_layout(close, mqtt_data):
    return create_layout(data)

if __name__ == '__main__':
    app.run_server(debug=True)
