
# Import recipe generation function and other required libraries 
from cgitb import text
import tkinter as tk
from tkinter import ttk

from transformers import FlaxAutoModelForSeq2SeqLM
from transformers import AutoTokenizer


MODEL_NAME_OR_PATH = "flax-community/t5-recipe-generation"
tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME_OR_PATH, use_fast=True)
model = FlaxAutoModelForSeq2SeqLM.from_pretrained(MODEL_NAME_OR_PATH)

prefix = "items: "
# generation_kwargs = {
#     "max_length": 512,
#     "min_length": 64,
#     "no_repeat_ngram_size": 3,
#     "early_stopping": True,
#     "num_beams": 5,
#     "length_penalty": 1.5,
# }
generation_kwargs = {
    "max_length": 512,
    "min_length": 64,
    "no_repeat_ngram_size": 3,
    "do_sample": True,
    "top_k": 60,
    "top_p": 0.95
}


special_tokens = tokenizer.all_special_tokens
tokens_map = {
    "<sep>": "--",
    "<section>": "\n"
}
def skip_special_tokens(text, special_tokens):
    for token in special_tokens:
        text = text.replace(token, "")

    return text.strip()


def target_postprocessing(texts, special_tokens):
    if not isinstance(texts, list):
        texts = [texts]

    new_texts = []
    for text in texts:
        text = skip_special_tokens(text, special_tokens)

        for k, v in tokens_map.items():
            text = text.replace(k, v)

        new_texts.append(text)

    return new_texts

def generation_function(texts):
    _inputs = texts if isinstance(texts, list) else [texts]
    inputs = [prefix + inp for inp in _inputs]
    inputs = tokenizer(
        inputs,
        max_length=256,
        padding="max_length",
        truncation=True,
        return_tensors="jax"
    )

    input_ids = inputs.input_ids
    attention_mask = inputs.attention_mask

    output_ids = model.generate(
        input_ids=input_ids,
        attention_mask=attention_mask,
        **generation_kwargs
    )
    generated = output_ids.sequences
    generated_recipe = target_postprocessing(
        tokenizer.batch_decode(generated, skip_special_tokens=False),
        special_tokens
    )
    return generated_recipe



def on_ok_click():
    # Initialize the items list to an empty list
    items = []
    headline=""
    outputlist = []
    # Get the input text from the Text widget and split it into a list
    input_paragraph = input_text.get("1.0", tk.END) #get input
    items.append(input_paragraph) #append into items list

    # Run the generation_function with the updated 'items' list
    generated = generation_function(items)
    for text in generated:
        sections = text.split("\n")
        for section in sections:
            section = section.strip()
            if section.startswith("title:"):    #replace the headers from the generated text (applys to title, ingredients and directions)
                section = section.replace("title:", "")
                headline = "RECIPE"
            elif section.startswith("ingredients:"):
                section = section.replace("ingredients:", "")
                headline = "INGREDIENTS"
            elif section.startswith("directions:"):
                section = section.replace("directions:", "")
                headline = "DIRECTIONS"
            
            #this is to append all replacements and the information together
            if headline == "RECIPE":
                title = f"[{headline}]: {section.strip().capitalize()}\n"
                topline = "-" * 30 
                bottomline = "-" * 30
                #outputlist.append(topline)
                outputlist.append(title)
                #outputlist.append(bottomline)

            else:
                section_info = [f"  - {i+1}: {info.strip().capitalize()}" for i, info in enumerate(section.split("--"))] #splits each instruction / ingredient by the "--" seperator in the generated.
                recipe = f"[{headline}]:\n" + "\n".join(section_info) +"\n" #joining the headline and the info
                outputlist.append(recipe) #appending each item, such as title, ingredients, direction and its respective info into a list

    # Format and display the generated recipe
    outputrecipe = "\n".join(outputlist) # concatenate each section with a line separator
    output_text.config(state='normal')  # Set the state to normal to enable editing temporarily
    output_text.delete("1.0", tk.END)  # Clear previous content
    output_text.insert(tk.END, outputrecipe) #insert fully joined recipe 
    output_text.config(state='disabled')  # Set the state back to disabled to make it read-only again


def on_exit_click():
    root.quit()

# Create the GUI
root = tk.Tk()
root.title('Recipe Generator')
root.configure(bg='white')

# Create a rounded style for the buttons
s = ttk.Style()
s.configure('Rounded.TButton', borderwidth=0, focuscolor='white', focusthickness=0, font=('Helvetica', 12))

main_frame = ttk.Frame(root, padding=10)
main_frame.pack(expand=True, fill='both')

input_label = ttk.Label(main_frame, text='Enter your Available Ingredients')
input_label.pack(pady=5)

# Use a Text widget for the multi-line input
input_text = tk.Text(main_frame, wrap=tk.WORD, width=30, height=5)
input_text.pack(pady=5)

output_label = ttk.Label(main_frame, text='Generated Recipe Goes Below:')
output_label.pack(pady=2)

output_text = tk.Text(main_frame, wrap=tk.WORD, width=80, height=20, state="disabled")
output_text.pack(pady=5)

# Centering the buttons in a new frame
button_frame = ttk.Frame(main_frame)
button_frame.pack(pady=10)

ok_button = ttk.Button(button_frame, text='Generate', style='Rounded.TButton', command=on_ok_click)
ok_button.pack(side=tk.LEFT, padx=5)

exit_button = ttk.Button(button_frame, text='Exit', style='Rounded.TButton', command=on_exit_click)
exit_button.pack(side=tk.RIGHT, padx=5)

# Set the background color using the style option
s.configure('Rounded.TButton', background='#87CEEB', foreground='dark blue')

root.mainloop()
