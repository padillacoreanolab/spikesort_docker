import gradio as gr 

def add_string(text: str, add: str) -> str:
    return text + add

iface = gr.Interface(
    fn=add_string,
    inputs=["text", "text"],
    outputs="text",
    title="Add String",
    description="Add a string to the end of your text."
)

iface.launch(server_name="0.0.0.0", server_port=7000)