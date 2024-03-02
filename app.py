import dash
import dash_bootstrap_components as dbc
from dash.dependencies import Input, Output
from dash import html, dcc
import json

app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP, '/assets/styles.css'])

# Load data from JSON file
with open('data.json', 'r') as file:
    data = json.load(file)

# Function to create a DBC Card with dynamic content
def create_card(card_data):
    overlay_info = card_data['overlay_info'][0] if card_data['overlay_info'] else ''
    info = [dbc.Col(html.P(info, className='card-text'), class_name='card-info-col') for info in card_data["overlay_info"]],
    info = info[0]
    return dbc.Card(
        [
            dbc.CardImg(src=card_data['background_image'], top=True, class_name="card-img"),
            dbc.CardBody(
                [
                    dbc.Row(html.H4(card_data['title'], className='card-title'), class_name='card-title-row'),
                    dbc.Row(children=info, class_name='card-info-row'),
                    # dbc.Row(html.P(overlay_info, className='card-text'), class_name='card-info-row'),  # Display the first element if available
                    dbc.Row(dbc.Button("Open Modal", id={'type': 'button', 'index': f'btn_{card_data["id"]}'}, color='primary', className='mr-2'), class_name='card-button-row'),
                ]
            ),
        ],
        id={'type': 'card', 'index': f'crd_{card_data["id"]}'},
    )


# Function to create a modal with dynamic content
def create_modal(card_id):
    card_data = next(card for card in data['cards'] if card['id'] == int(card_id.split('_')[1]))

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

    return dbc.Modal(
        [
            dbc.ModalHeader(card_data['title']),
            dbc.ModalBody(modal_content),
            dbc.ModalFooter(
                dbc.Button("Close", id='close-modal', className="ml-auto", n_clicks=0)
            ),
        ],
        id='modal',
        size=modal_size,
    )

# Layout of the app
app.layout = html.Div(
    [
        html.H1("Dash Card Grid"),
        dbc.Row(
            [dbc.Col(create_card(card)) for card in data['cards']],
        ),
        create_modal('crd_0'),
    ]
)

# Callback to open the modal on button click and close the modal
@app.callback(
    [Output('modal', 'is_open'), Output('modal', 'children')],
    Input({'type': 'button', 'index': 'ALL'}, 'n_clicks'),
    Input('close-modal', 'n_clicks'),
    prevent_initial_call=True,
)
def update_modal(n_clicks_button, n_clicks_close):
    ctx = dash.callback_context
    triggered_id = ctx.triggered_id

    print(f"Triggered ID: {triggered_id}")

    if triggered_id and 'index' in triggered_id['prop_id']:
        card_id = triggered_id['index']['index']
        print(f"Button Clicked - Card ID: {card_id}")
        return True, create_modal(card_id)

    elif triggered_id and triggered_id['prop_id'] == 'close-modal.n_clicks':
        print("Close Button Clicked")
        return False, None

    return False, None

if __name__ == '__main__':
    app.run_server(debug=True)
