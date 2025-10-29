import tkinter as tk

window = tk.Tk()
window.title("Calculator")
window.geometry("225x400")

entry = tk.Entry(window, width=20, font=("Arial", 12), borderwidth=2, relief="solid")
entry.grid(row=0, column=0, columnspan=4, padx=10, pady=10)

def button_click(symbol):
    entry.insert(tk.END, symbol)

def calculate():
    try:
        result = eval(entry.get())
        entry.delete(0, tk.END)
        entry.insert(0, result)
    except Exception:
        entry.delete(0, tk.END)
        entry.insert(0, "Ошибка")

def clear():
    entry.delete(0, tk.END)

buttons = [
    "7", "8", "9", "/",
    "4", "5", "6", "*",
    "1", "2", "3", "-",
    "0", ".", "=", "+"
]

row = 1
col = 0

for b in buttons:
    if b == "=":
        tk.Button(window, text=b, width=5, height=2, command=calculate).grid(row=row, column=col, padx=5, pady=5)
    else:
        tk.Button(window, text=b, width=5, height=2, command=lambda x=b: button_click(x)).grid(row=row, column=col,
                                                                                               padx=5, pady=5)
    col += 1
    if col > 3:
        col = 0
        row += 1

tk.Button(window, text="C", width=22, height=2, command=clear).grid(row=row, column=0, columnspan=4, padx=5, pady=5)
window.mainloop()