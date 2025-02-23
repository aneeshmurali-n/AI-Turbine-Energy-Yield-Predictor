from tkinter import *
from tkinter import messagebox
from tkinter import filedialog
import datetime
import pickle
from preprocessing import cap_outliers_iqr, square_transform, log1p_transform
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import FunctionTransformer, StandardScaler
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LinearRegression
import random
import json
import threading
import os
# define default config
default_config = {
    "main_bg": "#1e1f22",
    "entry_bg": "#26282e",
    "entry_fg": "#b7babf",
    "cursor_color": "#1e1f22",
    "selected_fg": "#c38fff",
    "head_label_fg": "#b7babf",
    "result_label_fg": "#b7babf",
    "label_fg": "#b7babf",
    "button_color": "#03dac6",
    "button_press_color": "#26282e",
    "button_text_color": "#1e1f22",
    "button_press_text_color": "#3e4047",
    "label_font_style": ["Ubuntu", 13, "italic"],
    "entry_font_style": ["Ubuntu", 13, "bold"],
    "result_label_font_style": ["Ubuntu", 15, "bold"],
    "head_label_font_style": ["Ubuntu", 13, "italic"],
    "button_font_style": ["Roboto", 13],
    "scrolled_text_font_style": ["Roboto", 11],
    "scrolled_text_bg": "#26282e",
    "scrolled_text_fg": "#9fa2a7",
    "scrolled_text_selected": "#664b86",
    "hover_effect_highlight_color": "#FFD700",
    "entry_highlight_bg_color": "#c38fff",
    "entry_highlight_fg_color": "#1e1f22",
    "report_title_text": "AMN Ai Turbine Performance and Energy Yield Report ",
    "button_press_delay": 150,
    "MWh_limit": 600,
    "working_hours": 8000,
    "afdp_display_unit" : "mbar",
    "cdp_display_unit" : "bar",
    "afdp_thresholds": {"low_sensor_error<": 0.5,"sensor_error_too_clean_filter<": 1.0,"clogging_warning_min>=": 3.5,"clogging_warning_max<=": 4.5,"clogged_filter>": 5.0},
    "tit_thresholds": {"critical_high": 1200,"very_high": 1150,"abnormal_high": 1100,"optimal_min": 900,"optimal_max": 1060},
    "cdp_thresholds": {"critically_low<": 9.5,"normal_min>=": 10.5,"normal_max<=": 13.5,"critically_high>": 15.5},
    "co_thresholds" : {"excellent<": 5.0,"efficient_max<=": 20.0,"moderate_max<=": 50.0}
}
# Load app configuration settings from the AMNai.json file and apply it or if not found generate new one with default settings
if not os.path.exists("AMNai.json"):
    with open("AMNai.json", "w") as new_settings:
        json.dump(default_config, new_settings, indent=4)
    config = default_config  # Use the default config
else:
    with open("AMNai.json", "r") as settings:
        config = json.load(settings)  # Load json config

main_bg = config["main_bg"]
entry_bg = config["entry_bg"]
entry_fg = config["entry_fg"]
cursor_color = config["cursor_color"]
selected_fg = config["selected_fg"]
head_label_fg = config["head_label_fg"]
result_label_fg = config["result_label_fg"]
label_fg = config["label_fg"]
button_color = config["button_color"]
button_press_color = config["button_press_color"]
button_text_color = config["button_text_color"]
button_press_text_color = config["button_press_text_color"]
label_font_style = tuple(config["label_font_style"])
entry_font_style = tuple(config["entry_font_style"])
result_label_font_style = tuple(config["result_label_font_style"])
head_label_font_style = tuple(config["head_label_font_style"])
button_font_style = tuple(config["button_font_style"])
scrolled_text_font_style = tuple(config["scrolled_text_font_style"])
scrolled_text_bg = config["scrolled_text_bg"]
scrolled_text_fg = config["scrolled_text_fg"]
report_title_text = config["report_title_text"]
MWh_limit = config["MWh_limit"] # if predicted tey is >= MWh_limit then show input unrealistic error message
working_hours = config["working_hours"] # 8000hours , the possible operational hours in a year considering maintenance break and repair services and all
hover_effect_highlight_color = config["hover_effect_highlight_color"]
entry_highlight_bg_color = config["entry_highlight_bg_color"]
entry_highlight_fg_color = config["entry_highlight_fg_color"]
button_press_delay = config["button_press_delay"]
scrolled_text_selected = config["scrolled_text_selected"]
afdp_display_unit = config["afdp_display_unit"]
cdp_display_unit = config["cdp_display_unit"]
low_sensor_error = config["afdp_thresholds"]["low_sensor_error<"]
sensor_error_too_clean_filter = config["afdp_thresholds"]["sensor_error_too_clean_filter<"]
clogging_warning_min = config["afdp_thresholds"]["clogging_warning_min>="]
clogging_warning_max = config["afdp_thresholds"]["clogging_warning_max<="]
tit_critical_high = config["tit_thresholds"]["critical_high"]
tit_very_high = config["tit_thresholds"]["very_high"]
tit_abnormal_high = config["tit_thresholds"]["abnormal_high"]
tit_optimal_min = config["tit_thresholds"]["optimal_min"]
tit_optimal_max = config["tit_thresholds"]["optimal_max"]
cdp_critically_low = config["cdp_thresholds"]["critically_low<"]
cdp_normal_min = config["cdp_thresholds"]["normal_min>="]
cdp_normal_max = config["cdp_thresholds"]["normal_max<="]
cdp_critically_high = config["cdp_thresholds"]["critically_high>"]
co_excellent = config["co_thresholds"]["excellent<"]
co_efficient_max = config["co_thresholds"]["efficient_max<="]
co_moderate_max = config["co_thresholds"]["moderate_max<="]
################################## Function definitions & Model Loading ################################################
# Function to generate text document
def doc_from_list_tuple(list_tuple):
    document =""
    for msg_and_action in list_tuple:
        document = document + f"\n{msg_and_action[0]}\n{msg_and_action[1]}\n"
    return document

report_doc=[] #([(msg1,action1),(msg2,action2),(msg3,action3),(etc)])

# Function to save Report
def save_report():
    window.focus_set() # remove focus from the entries
    date = datetime.date.today()
    if len(report_doc) > 0 : # if report doc generated
        doc_text = doc_from_list_tuple(report_doc)
        doc_text = report_title_text + str(date) +"\n\n"+ doc_text +"\n\n"# add title text and NOTE: and format it
        path_to_save_file = filedialog.asksaveasfilename(defaultextension=".txt",filetypes=[("Text files","*.txt")],initialfile=f"AMN AI TEY Report-{date}")
        if path_to_save_file:  # If the user doesn't cancel
            try:
                # Open the file in write mode and save the report text
                with open(path_to_save_file, 'w') as report:
                   report.write(doc_text)
                messagebox.showinfo("Save Successful", f"Report has been successfully saved at:\n\n{path_to_save_file}")
                return
            except Exception as e:
                messagebox.showerror("Save Failed",f"An error occurred while saving the file:\n\n{e}")
                return
        else:
            messagebox.showwarning("Save Canceled", "The save operation was canceled. No changes were made to your report.")
            return
    else:
        messagebox.showerror("Report Not Found","No report was generated. Please predict TEY first and try again.")
        return



# Function to clear output text labels
def clear_output_text_labels():
    global report_doc
    report_doc = []  # clear generated report if any
    result_label.config(text="")  # clear result label
    result_annual_tey_label.config(text="")  # clear  result_annual_tey_label label
    clear_report() # clear report scrolled text

# Function to convert unit returns tuple (value,'unit')
def auto_scale_mwh(tey_in_mwh):

    if tey_in_mwh >= 1000000:              # Convert to GWh if TEY >= 1,000,000 MWh
        tey_in_gwh = tey_in_mwh / 1000000  # Convert to GWh
        return tey_in_gwh, 'GWh'

    elif tey_in_mwh >= 1000:               # Convert to TWh if TEY >= 1,000 MWh and less than 1,000,000 MWh
        tey_in_twh = tey_in_mwh / 1000     # Convert to TWh
        return tey_in_twh, 'TWh'

    elif 0 < tey_in_mwh <= 999:           # If the value is between 0 and 999 MWh, return it as MWh
        return tey_in_mwh, 'MWh'

    else:                                  # If the value is not valid, return None
        return None, None

# Function to display text report window (scrolled text )
def display_report(text1,text2):
    report_text.config(state=NORMAL)
    report_text.insert(END, "\n"+ text1  + "\n"+ text2+"\n")
    report_text.config(state=DISABLED)

# Function to clear text report window (scrolled text )
def clear_report():
    report_text.config(state=NORMAL)
    report_text.delete(1.0, END)  # Deletes all text from the first line to the end
    report_text.config(state=DISABLED)

# Function to generate recommend action and report from the input data
# returns a list tuples of status and recommendation for every input arguments eg [(msg,action),(msg,action),(msg,action),(msg,action)]
def recommend_action(afdp, tit, cdp, co,exp_tey=None,tey_predicted=0.00):
    actions = []

    # Turbine Energy Yield (TEY)
    if exp_tey is None :
        msg = f'The Predicted Turbine Energy Yield is {round(tey_predicted, 2)} MWh, with an estimated Annual Energy Yield of {round(tey_predicted * working_hours, 2)} MWh based on {working_hours} hours of operation per year as a standard benchmark for estimating annual energy production.'
        action = 'Expected Turbine Energy Yield data was not provided for comparison analysis with the predicted Turbine Energy Yield.'
        actions.append((msg, action))
    else:
        # Turbine Energy Yield (TEY) comparison
        if tey_predicted < exp_tey * 0.9:
            msg = f'The Predicted Turbine Energy Yield is {round(tey_predicted,2)} MWh, which is below 90% of the Expected Turbine Energy Yield ({exp_tey} MWh). and the estimated Annual Energy Yield is {round(tey_predicted * working_hours,2)} MWh based on {working_hours} hours of operation per year as a standard benchmark for estimating annual energy production.'
            action = 'Investigate potential causes such as load reductions, operational inefficiencies, or fouling.'
            actions.append((msg, action))
        elif tey_predicted > exp_tey * 1.1:
            msg = f'The Predicted Turbine Energy Yield is {round(tey_predicted,2)} MWh, which exceeds 110% of the Expected Turbine Energy Yield ({exp_tey} MWh) and the estimated Annual Energy Yield is {round(tey_predicted * working_hours,2)} MWh based on {working_hours} hours of operation per year as a standard benchmark for estimating annual energy production.'
            action = 'Monitor turbine performance for any signs of overloading or unusual behavior.'
            actions.append((msg, action))
        else:
            msg = f'The Predicted Turbine Energy Yield is {round(tey_predicted,2)} MWh, within the expected range (±10% of Expected Turbine Energy Yield ({exp_tey} MWh) and estimated Annual Energy Yield is {round(tey_predicted * working_hours,2)} MWh based on {working_hours} hours of operation per year as a standard benchmark for estimating annual energy production.'
            action = 'No action required, continue monitoring.'
            actions.append((msg, action))


    # Air Filter Differential Pressure (AFDP)
    # "afdp_thresholds": {"low_sensor_error<": 0.5,"sensor_error_too_clean_filter<": 1.0,"clogging_warning_min>=": 3.5,"clogging_warning_max<=": 4.5}
    if afdp < low_sensor_error:
        msg = f'The Air Filter Differential Pressure is {afdp} {afdp_display_unit}, unusually low, potentially indicating a sensor error or improperly installed filter.'
        action = 'Inspect the airflow sensor and verify filter installation.'
        actions.append((msg, action))
    elif afdp < sensor_error_too_clean_filter:
        msg = f'The Air Filter Differential Pressure is {afdp} {afdp_display_unit}, which could indicate an airflow sensor error or the filter may be too clean.'
        action = 'Check airflow sensor for potential issues and verify that the filter is not excessively clean.'
        actions.append((msg, action))
    elif afdp < clogging_warning_min:
        msg = f'The Air Filter Differential Pressure is {afdp} {afdp_display_unit}, within the normal range.'
        action = 'No action required, continue monitoring.'
        actions.append((msg, action))
    elif clogging_warning_min <= afdp <= clogging_warning_max:
        msg = f'The Air Filter Differential Pressure is {afdp} {afdp_display_unit}, indicating that the filter is approaching clogging.'
        action = 'Monitor the filter closely and be prepared for cleaning or replacement.'
        actions.append((msg, action))
    else:
        msg = f'The Air Filter Differential Pressure is {afdp} {afdp_display_unit}, which indicates a clogged filter causing restricted airflow and efficiency losses.'
        action = 'Immediate action required: Clean or replace the air filter to restore optimal airflow and efficiency.'
        actions.append((msg, action))


    # Turbine Inlet Temperature (TIT)
    # "tit_thresholds": {"critical_high": 1200,"very_high": 1150,"abnormal_high": 1100,"optimal_min": 900,"optimal_max": 1060}
    if tit >= tit_critical_high:
        msg = f'The Turbine Inlet Temperature is {tit}°C, exceeding the critical limit of {tit_critical_high}°C, risking severe thermal damage.'
        action = 'Shut down the turbine immediately and investigate overheating causes.'
        actions.append((msg, action))
    elif tit >= tit_very_high:
        msg = f'The Turbine Inlet Temperature is {tit}°C, which is critically abnormal and presents a risk of overheating and potential thermal damage to components.'
        action = 'Immediate investigation of overheating risks is necessary.'
        actions.append((msg, action))
    elif tit >= tit_abnormal_high:
        msg = f'The Turbine Inlet Temperature is {tit}°C, which is abnormal and poses a risk of overheating and potential thermal damage to components.'
        action = 'Investigation of overheating risks is required.'
        actions.append((msg, action))
    elif tit >= tit_optimal_max:
        msg = f'The Turbine Inlet Temperature is {tit}°C, within the optimal performance range.'
        action = 'No action required, continue monitoring.'
        actions.append((msg, action))
    elif tit >= tit_optimal_min:
        msg = f'The Turbine Inlet Temperature is {tit}°C, which is at the lower end of the optimal range.'
        action = 'If the Turbine Inlet Temperature is consistently at the lower end, it may suggest underperformance or incomplete combustion.'
        actions.append((msg, action))
    else:
        msg = f'The Turbine Inlet Temperature is {tit}°C, which is below the optimal range and may indicate underperformance or incomplete fuel combustion.'
        action = 'Investigate potential issues with combustion or cooling systems.'
        actions.append((msg, action))


    # Compressor Discharge Pressure (CDP)
    # cdp_thresholds": {"critically_low<": 9.5,"normal_min>=": 10.5,"normal_max<=": 13.5,"critically_high>": 15.5}
    if cdp < cdp_critically_low:
        msg = f'The Compressor Discharge Pressure is critically low at {cdp} {cdp_display_unit}, suggesting air leakage, upstream blockages, or compressor failure.'
        action = 'Inspect for leaks, upstream blockages, or underperforming compressor.'
        actions.append((msg, action))
    elif cdp_critically_low <= cdp < cdp_normal_min:
        msg = f'The Compressor Discharge Pressure is {cdp} {cdp_display_unit}, slightly below normal, possibly due to ambient conditions or compressor issues.'
        action = 'Monitor trends, investigate if consistently low.'
        actions.append((msg, action))
    elif cdp_normal_min <= cdp <= cdp_normal_max:
        msg = f'The Compressor Discharge Pressure is {cdp} {cdp_display_unit}, within the normal operating range.'
        action = 'No action required, continue monitoring.'
        actions.append((msg, action))
    elif cdp_normal_max < cdp <= cdp_critically_high:
        msg = f'The Compressor Discharge Pressure is {cdp} {cdp_display_unit}, slightly above normal, possibly due to downstream resistance or compressor overloading.'
        action = 'Check for downstream fouling or blockages, verify compressor performance.'
        actions.append((msg, action))
    elif cdp > cdp_critically_high:
        msg = f'The Compressor Discharge Pressure is critically high at {cdp} {cdp_display_unit}, indicating severe downstream blockages or compressor issues.'
        action = 'Immediate action required: Inspect downstream systems and compressor components.'
        actions.append((msg, action))

    # Carbon Monoxide (CO) Emissions
    # "co_thresholds" : {"excellent<": 5.0,"efficient_max<=": 20.0,"moderate_max<=": 50.0}
    if co < co_excellent:
        msg = f'The Carbon Monoxide level is {co} mg/m³, indicating excellent combustion efficiency.'
        action = 'No action required, continue monitoring.'
        actions.append((msg, action))
    elif co_excellent<= co <= co_efficient_max:
        msg = f'The Carbon Monoxide level is {co} mg/m³, within the typical range for efficient combustion.'
        action = 'No immediate action required, but periodic monitoring is recommended.'
        actions.append((msg, action))
    elif co_efficient_max < co <= co_moderate_max:
        msg = f'The Carbon Monoxide level is {co} mg/m³, indicating moderate combustion inefficiency or transient conditions.'
        action = 'Check load conditions and monitor air/fuel ratio. Consider optimization if levels persist.'
        actions.append((msg, action))
    elif co > co_moderate_max:
        msg = f'The Carbon Monoxide level is {co} mg/m³, significantly above the acceptable range, indicating severe combustion inefficiency or a fault in the system.'
        action = 'Immediate action required: Inspect burners, optimize air/fuel ratio, and check for operational issues.'
        actions.append((msg, action))

    return actions



# This part is just for fun and make somthing interesting
error_messages = [
    {"title": "Uh-oh, something went wrong!", "message": "It looks like I couldn’t predict the Turbine Energy Yield. Please double-check your inputs and I’ll give it another shot!"},
    {"title": "I’m having trouble here.", "message": "It seems like some fields are missing or not quite right. Can you help me by correcting them? I’ll try again!"},
    {"title": "Whoops! Something’s off.", "message": "It looks like I need a bit more information to predict the yield. Check the fields, and I’ll give it another go!"},
    {"title": "I couldn’t quite get it this time.", "message": "Some of the fields seem to be incomplete or incorrect. Please check them and I’ll work on it again!"},
    {"title": "Hmm, I hit a bump.", "message": "It seems some input is missing or needs to be corrected. Can you help by filling it out? I’ll try again!"},
    {"title": "Oops, I ran into a problem!", "message": "I couldn’t predict the Turbine Energy Yield. Double-check the required fields and I’ll give it another try!"},
    {"title": "Something’s not quite right!", "message": "I wasn’t able to predict the yield. Please make sure everything is filled out correctly and let’s give it another try!"},
    {"title": "I’m stuck! Help me out.", "message": "Looks like some fields are incomplete or incorrect. Could you fix those for me? I’ll try again after that!"},
    {"title": "A little hiccup here!", "message": "I couldn’t generate the prediction. Please ensure all fields are correct and complete so I can try again!"},
    {"title": "Hold on, I’m having a moment.", "message": "It seems I can’t predict the Turbine Energy Yield right now. Can you review your inputs and try once more?"}
]

expected_tey_error_messages = [
    {"title": "I’m having trouble here.", "message": "It seems the input for the Expected Turbine Energy Yield isn’t a valid number. Could you check and try again?"},
    {"title": "Whoops! Something’s off.", "message": "The value entered for the Expected Turbine Energy Yield doesn’t appear to be a number. Please enter a valid number to proceed!"},
    {"title": "I couldn’t quite get it this time.", "message": "It looks like the Expected Turbine Energy Yield input isn’t a number. Could you double-check and try again?"},
    {"title": "Hmm, I hit a bump.", "message": "I couldn’t process the Expected Turbine Energy Yield because the input isn’t a number. Please enter a valid numeric value!"},
    {"title": "Oops, I ran into a problem!", "message": "It seems like the Expected Turbine Energy Yield input is not a valid number. Can you correct that and try again?"},
    {"title": "Something’s not quite right!", "message": "I couldn’t calculate the Expected Turbine Energy Yield because the input isn’t a valid number. Please check and try again!"},
    {"title": "I’m stuck! Help me out.", "message": "Looks like the input for the Expected Turbine Energy Yield isn’t a valid number. Could you enter a valid numeric value?"},
    {"title": "A little hiccup here!", "message": "It seems the Expected Turbine Energy Yield value you entered isn’t a number. Could you provide a valid numeric input?"},
    {"title": "Hold on, I’m having a moment.", "message": "The input for the Expected Turbine Energy Yield seems invalid. I need a valid number to continue. Could you check it?"}
]

# Pop different error message each time for wrong input entry
def show_input_error():
    message = random.choice(error_messages) # pick different message each time
    messagebox.showerror(message['title'],message['message'])

# Pop different error message each time for wrong optional expected_tey entry
def show_expected_tey_input_error():
    message = random.choice(expected_tey_error_messages) # pick different message each time
    messagebox.showerror(message['title'],message['message'])

#_______________________________________________________________________________________________________________________

############################################ Load the pipeline #########################################################
with open('turbine_energy_yield_prediction_model_by_amn.pkl', 'rb') as file:
    model = pickle.load(file)
#_______________________________________________________________________________________________________________________

############################ Main Function to predict TEY and Generate Report ##########################################
expected_tey = None
def predict_tey():
    window.focus_set() # remove focus from the entries
    global report_doc
    global expected_tey
    data = expected_tey_entry.get()
    if len(data) != 0:
        generated_error_message = f"It looks like you entered {data}. The Expected Turbine Energy Yield needs to be a positive value greater than zero.\nCould you check it and try again."
        # Try to convert to float, if it breaks then run except block
        try:
            expected_tey = float(data)
            if expected_tey <= 0:
                raise ValueError(generated_error_message)
        except ValueError as e:
            if str(e) == generated_error_message:
                messagebox.showerror("Oops! You entered an invalid value", generated_error_message)
                return
            else:
                show_expected_tey_input_error() # pop show_expected_tey_input_error messages
                return

    else:
        expected_tey = None # if it's empty set None cause the function "recommend_action(afdp, tit, cdp, co,expected_tey=None,tey_predicted=0.00)" logic handles it

    try:
        afdp = float(afdp_entry.get())
        tit = float(tit_entry.get())
        cdp = float(cdp_entry.get())
        co = float(co_entry.get())
        input_data = pd.DataFrame({
            'AFDP': [afdp],
            'TIT': [tit],
            'CDP': [cdp],
            'CO': [co]
        })

        # Make prediction of Turbine Energy Yield from the input data
        prediction = model.predict(input_data)[0]

        # auto_scale predicted tey into different scales like TWh,GWh,MWh also return None when the value is negative or zero
        value, unit = auto_scale_mwh(prediction)
        if value is None or unit is None or prediction>= MWh_limit:  # if None or greater than TEY limit show message and clear output text else continue
            clear_output_text_labels()
            messagebox.showerror("Whoops! Something’s off.","Entered Inputs seems to be Unrealistic, Could you check it?")
            return

        else:
            # Clear output text labels also clear report_doc variable which keeps the report information to save on a text file when save report button is pressed
            clear_output_text_labels()

            # Update result labels
            auto_scaled_tey = auto_scale_mwh(prediction)
            result_label.config(text=f'{auto_scaled_tey[0]:.2f} {auto_scaled_tey[1]}')  # ({value}{unit})
            auto_scaled_aey = auto_scale_mwh(prediction * working_hours)
            result_annual_tey_label.config(text=f'{auto_scaled_aey[0]:.2f} {auto_scaled_aey[1]}')

            # Generate report
            report_doc = recommend_action(afdp=afdp, tit=tit, cdp=cdp, co=co, exp_tey=expected_tey, tey_predicted=prediction)
            # Generate end note
            end_note = "Note:\nPlease disregard this message if the parameters have already been correctly set.\n\nThe alert thresholds in this system serve as general guidelines and may vary depending on the turbine model, design specifications, and operational conditions. To ensure accurate monitoring and effective alerts, it is important to adjust the threshold parameters in the AMNai.json configuration file. Parameters such as afdp_thresholds, co_thresholds, tit_thresholds, and cdp_thresholds should be customized to reflect the specific characteristics and performance requirements of the turbine. Proper adjustments will help achieve optimal system performance and precise diagnostics."

            # Display report
            for msg, recommend_actions in report_doc:
                display_report(msg, recommend_actions)
            display_report("",end_note)   # display end note, this just for displaying warning in the scrolled_text report window, and it's not be printed on the exported report file



        ####################################################################################################################################################################################################

    except ValueError:
        clear_output_text_labels()
        show_input_error()
        return

#-----------------------------------------------------------------------------------------------------------------------

# Function to close the window when the user clicks the "X" button
def destroy():
    window.destroy()

# Function to clear focus on widgets when clicked on empty area
def on_left_click(event):
    # Check clicked on the window empty space
    widget = window.winfo_containing(event.x_root, event.y_root)
    if widget == window:  # If clicked on the window empty space
        window.focus_set()

def set_focus_to_first_entry(event):
    afdp_entry.focus_set()

# When Up arrow is pressed, move focus to the previous Entry widget
def move_focus_up(event, current_entry, previous_entry):
    previous_entry.focus()

# When Down arrow is pressed, move focus to the next Entry widget
def move_focus_down(event, current_entry, next_entry):
    next_entry.focus()


# When ctrl + p is pressed invoke predict_button
def on_ctrl_p(event):
    predict_button.invoke()

# When ctrl + s is pressed invoke save report button
def on_ctrl_s(event):
    save_report_button.invoke()

# When ctrl + delete pressed clear all output labels
def on_delete(event):
    clear_output_text_labels()
    window.focus_set()         # clear focus

# button hover effects
def on_enter(event):
    event.widget.config(bg=hover_effect_highlight_color,fg=main_bg)  # Highlight on hover

def on_leave(event):
    event.widget.config(bg=button_color,fg=button_text_color)  # Revert back on leave

# entry on focus effect
def on_focus_in(event):
    event.widget.config(fg=entry_highlight_fg_color,bg=entry_highlight_bg_color)  # Change colors when focused

def on_focus_out(event):
    event.widget.config(fg=entry_fg,bg=entry_bg)  # Restore colors when not focused


# This function is used for Predict TEY button click and keyboard shortcut
def predict_button_click():
    predict_button.config(bg=button_press_color,fg=button_press_text_color)
    threading.Thread(target=lambda : predict_tey()).start() # call predict_tey in thread
    window.after(button_press_delay, lambda: predict_button.config(bg=button_color,fg=button_text_color)) # After a short delay, change the color back to normal # window.after(ms,function)

# save report
def save_button_click():
    save_report_button.config(bg=button_press_color,fg=button_press_text_color)
    threading.Thread(target=lambda : save_report()).start()  # call save_report in thread
    window.after(button_press_delay, lambda: save_report_button.config(bg=button_color,fg=button_text_color))

################################################## Create main window ##################################################
window = Tk()
window.geometry("1315x450")
window.resizable(False, False)
window.title("AMN Ai Turbine Energy Yield Predictor")
window.config(bg=main_bg)  # set the window background color
window.wm_protocol("WM_DELETE_WINDOW", destroy)  # When the user clicks the "X" button call destroy Function
window.iconbitmap(r'icon.ico')  # Set the window icon

################################################## Input fields ########################################################
afdp_label = Label(window, text=f"Air Filter Difference Pressure ({afdp_display_unit}):", bg=main_bg, fg=label_fg, font=label_font_style) # AFDP
afdp_label.grid(row=0, column=0, sticky="e",pady=(35,2))

afdp_entry = Entry(window,bg=entry_bg,fg=entry_fg, border=0, font=entry_font_style, justify="center",insertbackground=cursor_color,selectbackground=entry_highlight_bg_color,selectforeground=selected_fg)
afdp_entry.grid(row=0, column=1,pady=(35,2))

tit_label = Label(window, text="Turbine Inlet Temperature (°C):", bg=main_bg, fg=label_fg, font=label_font_style) # TIT
tit_label.grid(row=1, column=0, sticky="e", pady=(1,2))

tit_entry = Entry(window, bg=entry_bg, fg=entry_fg,border=0, font=entry_font_style, justify="center", insertbackground=cursor_color,selectbackground=entry_highlight_bg_color,selectforeground=selected_fg)
tit_entry.grid(row=1, column=1, pady=(1,2))

cdp_label = Label(window, text=f"         Compressor Discharge Pressure ({cdp_display_unit}):", bg=main_bg, fg=label_fg, font=label_font_style) # CDP
cdp_label.grid(row=2, column=0, sticky="e", pady=(1,2))

cdp_entry = Entry(window,bg=entry_bg, fg=entry_fg,border=0, font=entry_font_style, justify="center", insertbackground=cursor_color,selectbackground=entry_highlight_bg_color,selectforeground=selected_fg)
cdp_entry.grid(row=2, column=1, pady=(1,2))

co_label = Label(window, text="Carbon Monoxide (mg/m³):", bg=main_bg, fg=label_fg, font=label_font_style) # CO
co_label.grid(row=3, column=0, sticky="e", pady=(1,2))

co_entry = Entry(window,bg=entry_bg,fg=entry_fg, border=0, font=entry_font_style, justify="center", insertbackground=cursor_color,selectbackground=entry_highlight_bg_color,selectforeground=selected_fg)
co_entry.grid(row=3, column=1, pady=(1,2))

expected_tey_label = Label(window, text="Expected Turbine Energy Yield to compare with predicted TEY (MWh):", bg=main_bg, fg=label_fg, font=label_font_style) # expected_tey
expected_tey_label.grid(row=6, column=2, sticky="e", pady=(1,1),padx=10)

expected_tey_entry = Entry(window,bg=entry_bg,fg=entry_fg, border=0, font=entry_font_style, justify="center", insertbackground=cursor_color,selectbackground=entry_highlight_bg_color,selectforeground=selected_fg)
expected_tey_entry.grid(row=6, column=3, sticky="e",pady=(1,2), padx=10)

####################################################### Output fields ##################################################

# Result label head tey
result_label_head = Label(window, text="Predicted Turbine Energy Yield:", bg=main_bg,fg=head_label_fg, font=head_label_font_style)
result_label_head.grid(row=5, column=0, sticky="e",pady=(1,2))

# Result label tey
result_label = Label(window, text="", bg=main_bg,fg=result_label_fg, font=result_label_font_style)
result_label.grid(row=5, column=1, sticky="nsew",pady=(1,2))

# Result label head tey annual
result_annual_tey_label_head = Label(window, text="Estimated Annual Energy Yield:", bg=main_bg,fg=head_label_fg, font=head_label_font_style)
result_annual_tey_label_head.grid(row=6, column=0, sticky="e",pady=(1,2))

# Result label tey annual
result_annual_tey_label = Label(window, text="", bg=main_bg,fg=result_label_fg, font=result_label_font_style)
result_annual_tey_label.grid(row=6, column=1, sticky="nsew",pady=(1,2))

# Report window scrolled text box
report_text = Text(window, wrap=WORD,bg=scrolled_text_bg, fg=scrolled_text_fg,height=10, width=40,font=scrolled_text_font_style,selectbackground=scrolled_text_bg,selectforeground=scrolled_text_selected,bd=0)  # bd=0 removes the border
report_text.grid(row=0, column=2, rowspan=6, columnspan=2, sticky="nsew", padx=10, pady=42)

##################################################### button and binds #################################################
#Prediction button
predict_button = Button(window, text="Predict TEY", command=predict_button_click,height=1, width=10,bg=button_color,fg=button_text_color,font=button_font_style, border=0, relief="flat",activebackground=button_press_color,activeforeground=button_press_text_color)
predict_button.grid(row=7, column=3,sticky="ew",padx=10,pady=3)

#Save Report button
save_report_button = Button(window, text="Save Report", command=save_button_click,height=1, width=10,bg=button_color,fg=button_text_color,font=button_font_style, border=0, relief="flat",activebackground=button_press_color,activeforeground=button_press_text_color)
save_report_button.grid(row=8, column=3,sticky="ew",padx=10,pady=3)

# Bind the Up and Down Arrow keys for navigation between entries
afdp_entry.bind("<Down>", lambda event: move_focus_down(event, afdp_entry, tit_entry))
tit_entry.bind("<Down>", lambda event: move_focus_down(event, tit_entry, cdp_entry))
cdp_entry.bind("<Down>", lambda event: move_focus_down(event, cdp_entry, co_entry))
co_entry.bind("<Down>", lambda event: move_focus_down(event, co_entry, expected_tey_entry))

expected_tey_entry.bind("<Up>", lambda event: move_focus_up(event, expected_tey_entry, co_entry))
co_entry.bind("<Up>", lambda event: move_focus_up(event, co_entry, cdp_entry))
cdp_entry.bind("<Up>", lambda event: move_focus_up(event, cdp_entry, tit_entry))
tit_entry.bind("<Up>", lambda event: move_focus_up(event, tit_entry,afdp_entry ))

# Bind the enter key for navigate down through entries
afdp_entry.bind("<Return>", lambda event: move_focus_down(event, afdp_entry, tit_entry))
tit_entry.bind("<Return>", lambda event: move_focus_down(event, tit_entry, cdp_entry))
cdp_entry.bind("<Return>", lambda event: move_focus_down(event, cdp_entry, co_entry))
co_entry.bind("<Return>", lambda event: move_focus_down(event, co_entry, expected_tey_entry))  # Move to expected_tey_entry


# Bind te  ctrl + delete or d key to trigger on_delete event (clear all output labels, scrolled text and generated report_doc)
window.bind("<Control-Delete>", on_delete)
window.bind("<Control-D>", on_delete)
window.bind("<Control-d>", on_delete)

window.bind("<Control-p>", on_ctrl_p) # predict tey predict_button_click()
window.bind("<Control-s>", on_ctrl_s) # save report save_button_click()
window.bind("<Control-P>", on_ctrl_p) # predict tey predict_button_click()
window.bind("<Control-S>", on_ctrl_s) # save report save_button_click()

window.bind("<Button-1>", on_left_click)

# bind for hover effect
predict_button.bind("<Enter>", on_enter)
predict_button.bind("<Leave>", on_leave)
save_report_button.bind("<Enter>", on_enter)
save_report_button.bind("<Leave>", on_leave)

# Bind focus in and out events to entry widgets for highlight_effect
afdp_entry.bind("<FocusIn>", on_focus_in)
afdp_entry.bind("<FocusOut>", on_focus_out)

tit_entry.bind("<FocusIn>", on_focus_in)
tit_entry.bind("<FocusOut>", on_focus_out)

cdp_entry.bind("<FocusIn>", on_focus_in)
cdp_entry.bind("<FocusOut>", on_focus_out)

co_entry.bind("<FocusIn>", on_focus_in)
co_entry.bind("<FocusOut>", on_focus_out)

expected_tey_entry.bind("<FocusIn>", on_focus_in)
expected_tey_entry.bind("<FocusOut>", on_focus_out)

window.bind("<Control-f>",set_focus_to_first_entry)
window.bind("<Control-F>",set_focus_to_first_entry)

# Start the window
window.mainloop()