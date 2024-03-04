import dash
import dash_bootstrap_components as dbc
from dash.dependencies import Input, Output, State
from dash import html, dcc, ALL, Patch
import json
import paho.mqtt.client as mqtt
import socket
from datetime import datetime
import dash_mantine_components as dmc
from dash_iconify import DashIconify

app = dash.Dash(__name__, update_title=None ,external_stylesheets=[dbc.themes.BOOTSTRAP, '/assets/styles.css', "https://use.fontawsome.com/releases/v5.7.2/css/all.css"])

# Load data from JSON file
with open('data.json', 'r', encoding="utf-8") as file:
    data = json.load(file)

store = dcc.Store(data={}, id="data", storage_type='memory')

# MQTT configuration
mqtt_broker = data["mqtt"]["broker"]
mqtt_username = data["mqtt"]["user"]  # Replace with your MQTT broker username
mqtt_password = data["mqtt"]["password"]  # Replace with your MQTT broker password

# get mqtt topics
mqtt_topics = set()
btn_states = []

btn_lookup = {
    "id2cmd" : {},
    "id2state" : {},
    "state2id" : {},
    "id2n" : {}
}

c = 0
for card in data["cards"]:
    for card_dat in card["overlay_info"]:
        mqtt_topics.add(card_dat["topic"].split("/")[0] + "/#")
    for k in card["modal_content"]:
        match k:
            case "buttons":
                i=0
                for btn in card["modal_content"][k]:
                    btn_id = f'modal-btn_{card["id"]}_{i}'
                    if "cmd_topic" in btn.keys():
                        mqtt_topics.add(btn["cmd_topic"].split("/")[0] + "/#")
                        btn_lookup["id2cmd"][btn_id] = btn["cmd_topic"]
                    if "state_topic" in btn.keys():
                        mqtt_topics.add(btn["state_topic"].split("/")[0] + "/#")
                        btn_states.append(btn["state_topic"])
                        btn_lookup["id2state"][btn_id] = btn["state_topic"]
                        btn_lookup["state2id"][btn["state_topic"]] = btn_id
                        
                    btn_lookup["id2n"][btn_id] = c+i
                    i += 1

    c += 1
# MQTT callback function
def on_message(client, userdata, msg):
    global store
    # initial_temperature = msg.payload.decode("utf-8")
    store.data[msg.topic] = msg.payload.decode("utf-8")
    # update_layout(None)

# Set up MQTT client with optional username and password
client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
client.username_pw_set(username=mqtt_username, password=mqtt_password)
client.on_message = on_message
client.connect(mqtt_broker, data["mqtt"]["port"], 60)
for mqtt_topic in mqtt_topics:
    client.subscribe(mqtt_topic)
client.loop_start()



def send_mqtt_msg(topic, payload=True, client=client):
    client.publish(topic, payload=payload)



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
        btns = []
        btns1 = []
        i = 0
        for button in card_data['modal_content']['buttons']:
            if "icon" in button.keys():
                btn = dmc.Button(
                    button["title"],
                    rightIcon=DashIconify(icon="fluent-emoji-flat:light-bulb", width=button["width"]),
                    size="md",
                    id={'type': 'modal-button', 'index': f'modal-btn_{card_data["id"]}_{i}'},
                    color="grey"
                ),
            else:
                btn = dmc.Button(
                    button["title"],
                    size="md",
                    id={'type': 'modal-button', 'index': f'modal-btn_{card_data["id"]}_{i}'},
                    color="grey"
                ),
            i += 1
            # btns.extend(btn)
            btns1.append(dbc.Col(btn, className="md-c"))
            # btns1.extend(btn)

        # btns = [dbc.Button(button["title"], color='primary', className='mr-2') for button in card_data['modal_content']['buttons']]
        modal_content.append(dbc.Row(children=btns1, className="md-r"))
        # modal_content.extend(btns1)

    modal_content.append(dbc.Row(dmc.Divider(variant="solid"), className="md-r"))

    # # Dropdowns
    # if 'dropdowns' in card_data['modal_content']:
    #     modal_content.extend([dbc.DropdownMenu(
    #         label='Dropdown',
    #         children=[
    #             dbc.DropdownMenuItem(option, id=f'dropdown-{card_id}-{i}', n_clicks=0) for i, option in enumerate(dropdown['options'])
    #         ],
    #     ) for dropdown in card_data['modal_content']['dropdowns']])

    # modal_content.extend(dbc.Row(dmc.Divider(variant="solid"), className="md-r"))
    

    # # Radio Buttons
    # if 'radio_buttons' in card_data['modal_content']:
    #     modal_content.extend([dbc.RadioItems(
    #         options=[{'label': option, 'value': option} for option in radio['options']],
    #         value=radio['default'],
    #         inline=True,
    #     ) for radio in card_data['modal_content']['radio_buttons']])

    # modal_content.extend(dbc.Row(dmc.Divider(variant="solid"), className="md-r"))
    

    # Sliders
    if 'sliders' in card_data['modal_content']:
        slider = [dbc.Col(dmc.Slider(
            min=slider["min"], 
            max=slider["max"], 
            step=slider["step"],
        ),className="md-c")  for slider in card_data['modal_content']['sliders']]
        modal_content.append(dbc.Row(slider, class_name="md-r"))

    modal_content.append(dbc.Row(dmc.Divider(variant="solid"), className="md-r"))
    

    # # Iframes
    # if 'iframes' in card_data['modal_content']:
    #     modal_content.extend([html.Iframe(src=iframe, width='100%', height='400px') for iframe in card_data['modal_content']['iframes']])

    modal_size = 'sm'

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


def create_main_info(info):

    all_info = []
    for tmp_info in info:
        if "topic" in tmp_info.keys() and tmp_info["topic"] in store.data.keys():
            if "unit" in tmp_info.keys():
                info_content = store.data[tmp_info["topic"]] + " " + tmp_info["unit"]
            else:
                info_content = store.data[tmp_info["topic"]]
        else:
            if "unit" in tmp_info.keys():
                info_content = tmp_info["content"] + " " +tmp_info["unit"]
            else:
                if ":" in tmp_info["content"]:
                    info_content = datetime.now().strftime(tmp_info["content"])
                else:   
                    info_content = tmp_info["content"]
        all_info.append(dbc.Col([dbc.Col(html.P(tmp_info["title"], className='info-title')), dbc.Col(html.P(info_content, className='info-content'))], class_name='card-info-col'))
    return all_info


def create_layout(data, layout=None):
    # if not layout is None:
    #     layout = Patch()
    #     return layout
    # Layout of the app
    modals = []

    for card in data["cards"]:
        mod = create_modal(card["id"])
        modals.append(mod)
        
    layout = [
        dbc.Row(dbc.Col(html.H1(data["title"])), className="app-title"),
        dbc.Row(create_main_info(data["main_info"]), className="main-info-row"),
        dbc.Row(
            [dbc.Col(create_card(card)) for card in data['cards']],
        ),
        *modals,
        store,
        dcc.Interval(
            id='update-rate',
            interval=2.0*1e3,  # in milliseconds, update every 10 seconds
            n_intervals=0
        ),
    ]

    return layout
    

app.layout = html.Div(
    create_layout(data),
    id="app-layout"
)

mod_outputs = []
mod_states = []

mod_btns_states = []
mod_btns_css_cls = []

for card in data["cards"]:
    mod_outputs.append(Output("modal_"+str(card["id"]), "is_open"))
    mod_states.append(State("modal_"+str(card["id"]), "is_open"))

    for k in card["modal_content"].keys():
        match k:
            case "buttons":
                btn_i = 0
                for btns in card["modal_content"][k]:
                    btn_id = {'type': 'modal-button', 'index': f'modal-btn_{card["id"]}_{btn_i}'}
                    mod_btns_states.append(State(btn_id, "color"))
                    mod_btns_css_cls.append(Output(btn_id, "color"))
                    btn_i += 1

print("finish")
# Callback to open the modal on button click and close the modal
@app.callback(
    mod_outputs,
    Input({'type': 'button', 'index': ALL}, 'n_clicks'),
    # Input({'type': 'close-modal-button', 'index': ALL}, 'n_clicks'),
    prevent_initial_call=True,
)
def open_modal(n_clicks_button):
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
    
@app.callback(
    *mod_btns_css_cls,
    Input({'type': 'modal-button', 'index': ALL}, 'n_clicks'),
    Input("update-rate", "n_intervals"),
    *mod_btns_states,
    prevent_initial_call=True,   
)

def mod_button_cmd(*args):
    payl = False
    def_col = ["grey"] * len(mod_btns_states)
    ctx = dash.callback_context
    triggered_id = ctx.triggered_id
    if type(triggered_id) == type(""):
        for st_topic in btn_states:
            if st_topic in store.data.keys():
                bn_id = btn_lookup["state2id"][st_topic]
                btn_n = btn_lookup["id2n"][bn_id]
                if store.data[st_topic] == "true":    
                    def_col[btn_n] = "green"
                else:
                    def_col[btn_n] = "grey"
            return def_col
    btn_id = triggered_id["index"]
    card_n = int(btn_id.split("_")[-2])
    btn_n = int(btn_id.split("_")[-1])
    tmp_state = btn_lookup["id2state"][btn_id]
    if tmp_state in store.data.keys():
        if store.data[tmp_state] == "true":
            payl = False
        else:
            payl = True
    tmp_topic = data["cards"][card_n]["modal_content"]["buttons"][btn_n]["cmd_topic"]
    send_mqtt_msg(topic=tmp_topic, payload=payl)
    
    return def_col

@app.callback(
    Output("app-layout", "children"),
    Input({'type': 'close-modal-button', 'index': ALL}, 'n_clicks'),
    Input("update-rate", "n_intervals"),
    *mod_states,
)

def update_layout(close, int, *args):
    #check if None in args
    ctx = dash.callback_context
    triggered_id = ctx.triggered_id

    if any(args):
        if type(triggered_id) != type(""):   
            return create_layout(data)    
        else:
            return dash.no_update
    else:
        return create_layout(data)
if __name__ == '__main__':
    app.run_server(debug=True, use_reloader=True)
    # app.run_server(host="192.168.188.20", port=8050, debug=False, use_debugger=False, use_reloader=False)
