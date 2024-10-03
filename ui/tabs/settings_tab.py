import shutil
import os
import gradio as gr
import boop.globals
import ui.globals
from boop.utilities import clean_dir

available_themes = ["Default", "gradio/glass", "gradio/monochrome", "gradio/seafoam", "gradio/soft", "gstaff/xkcd", "freddyaboulton/dracula_revamped", "ysharma/steampunk"]
image_formats = ['jpg','png', 'webp']
video_formats = ['avi','mkv', 'mp4', 'webm']
video_codecs = ['libx264', 'libx265', 'libvpx-vp9', 'h264_nvenc', 'hevc_nvenc']
providerlist = None

settings_controls = []

def settings_tab():
    from boop.core import suggest_execution_providers
    global providerlist

    providerlist = suggest_execution_providers()
    with gr.Tab("⚙ Settings"):
        with gr.Row():
            with gr.Column():
                themes = gr.Dropdown(available_themes, label="Theme", info="Change needs complete restart", value=boop.globals.CFG.selected_theme)
            with gr.Column():
                settings_controls.append(gr.Checkbox(label="Public Server", value=boop.globals.CFG.server_share, elem_id='server_share', interactive=True))
                settings_controls.append(gr.Checkbox(label='Clear output folder before each run', value=boop.globals.CFG.clear_output, elem_id='clear_output', interactive=True))
                output_template = gr.Textbox(label="Filename Output Template", info="(file extension is added automatically)", lines=1, placeholder='{file}_{time}', value=boop.globals.CFG.output_template)
            with gr.Column():
                input_server_name = gr.Textbox(label="Server Name", lines=1, info="Leave blank to run locally", value=boop.globals.CFG.server_name)
            with gr.Column():
                input_server_port = gr.Number(label="Server Port", precision=0, info="Leave at 0 to use default", value=boop.globals.CFG.server_port)
        with gr.Row():
            with gr.Column():
                settings_controls.append(gr.Dropdown(providerlist, label="Provider", value=boop.globals.CFG.provider, elem_id='provider', interactive=True))
                chk_det_size = gr.Checkbox(label="Use default Det-Size", value=True, elem_id='default_det_size', interactive=True)
                settings_controls.append(gr.Checkbox(label="Force CPU for Face Analyser", value=boop.globals.CFG.force_cpu, elem_id='force_cpu', interactive=True))
                max_threads = gr.Slider(1, 32, value=boop.globals.CFG.max_threads, label="Max. Number of Threads", info='default: 3', step=1.0, interactive=True)
            with gr.Column():
                memory_limit = gr.Slider(0, 128, value=boop.globals.CFG.memory_limit, label="Max. Memory to use (Gb)", info='0 meaning no limit', step=1.0, interactive=True)
                settings_controls.append(gr.Dropdown(image_formats, label="Image Output Format", info='default: png', value=boop.globals.CFG.output_image_format, elem_id='output_image_format', interactive=True))
            with gr.Column():
                settings_controls.append(gr.Dropdown(video_codecs, label="Video Codec", info='default: libx264', value=boop.globals.CFG.output_video_codec, elem_id='output_video_codec', interactive=True))
                settings_controls.append(gr.Dropdown(video_formats, label="Video Output Format", info='default: mp4', value=boop.globals.CFG.output_video_format, elem_id='output_video_format', interactive=True))
                video_quality = gr.Slider(0, 100, value=boop.globals.CFG.video_quality, label="Video Quality (crf)", info='default: 14', step=1.0, interactive=True)
            with gr.Column():
                with gr.Group():
                    settings_controls.append(gr.Checkbox(label='Use OS temp folder', value=boop.globals.CFG.use_os_temp_folder, elem_id='use_os_temp_folder', interactive=True))
                    settings_controls.append(gr.Checkbox(label='Show video in browser (re-encodes output)', value=boop.globals.CFG.output_show_video, elem_id='output_show_video', interactive=True))
                button_apply_restart = gr.Button("Restart Server", variant='primary')
                button_clean_temp = gr.Button("Clean temp folder")
                button_apply_settings = gr.Button("Apply Settings")

    chk_det_size.select(fn=on_option_changed)

    # Settings
    for s in settings_controls:
        s.select(fn=on_settings_changed)
    max_threads.input(fn=lambda a,b='max_threads':on_settings_changed_misc(a,b), inputs=[max_threads])
    memory_limit.input(fn=lambda a,b='memory_limit':on_settings_changed_misc(a,b), inputs=[memory_limit])
    video_quality.input(fn=lambda a,b='video_quality':on_settings_changed_misc(a,b), inputs=[video_quality])

    # button_clean_temp.click(fn=clean_temp, outputs=[bt_srcfiles, input_faces, target_faces, bt_destfiles])
    button_clean_temp.click(fn=clean_temp)
    button_apply_settings.click(apply_settings, inputs=[themes, input_server_name, input_server_port, output_template])
    button_apply_restart.click(restart)


def on_option_changed(evt: gr.SelectData):
    attribname = evt.target.elem_id
    if isinstance(evt.target, gr.Checkbox):
        if hasattr(boop.globals, attribname):
            setattr(boop.globals, attribname, evt.selected)
            return
    elif isinstance(evt.target, gr.Dropdown):
        if hasattr(boop.globals, attribname):
            setattr(boop.globals, attribname, evt.value)
            return
    raise gr.Error(f'Unhandled Setting for {evt.target}')


def on_settings_changed_misc(new_val, attribname):
    if hasattr(boop.globals.CFG, attribname):
        setattr(boop.globals.CFG, attribname, new_val)
    else:
        print("Didn't find attrib!")
        


def on_settings_changed(evt: gr.SelectData):
    attribname = evt.target.elem_id
    if isinstance(evt.target, gr.Checkbox):
        if hasattr(boop.globals.CFG, attribname):
            setattr(boop.globals.CFG, attribname, evt.selected)
            return
    elif isinstance(evt.target, gr.Dropdown):
        if hasattr(boop.globals.CFG, attribname):
            setattr(boop.globals.CFG, attribname, evt.value)
            return
            
    raise gr.Error(f'Unhandled Setting for {evt.target}')

def clean_temp():
    from ui.main import prepare_environment
    
    ui.globals.ui_input_thumbs.clear()
    boop.globals.INPUT_FACESETS.clear()
    boop.globals.TARGET_FACES.clear()
    ui.globals.ui_target_thumbs = []
    if not boop.globals.CFG.use_os_temp_folder:
        clean_dir(os.environ["TEMP"])
    prepare_environment()
    gr.Info('Temp Files removed')
    return None,None,None,None


def apply_settings(themes, input_server_name, input_server_port, output_template):
    from ui.main import show_msg

    boop.globals.CFG.selected_theme = themes
    boop.globals.CFG.server_name = input_server_name
    boop.globals.CFG.server_port = input_server_port
    boop.globals.CFG.output_template = output_template
    boop.globals.CFG.save()
    show_msg('Settings saved')


def restart():
    ui.globals.ui_restart_server = True
