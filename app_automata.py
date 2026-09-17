import json
import tkinter as tk
from tkinter import filedialog, scrolledtext, messagebox
from collections import deque
from graphviz import Digraph
from PIL import Image, ImageTk

# ==========================================
# 0. Función Auxiliar para crear Tablas ASCII
# ==========================================
def format_table(headers, rows):
    if not rows:
        rows = [["-" for _ in headers]]
    col_widths = [len(str(h)) for h in headers]
    for row in rows:
        for i, cell in enumerate(row):
            col_widths[i] = max(col_widths[i], len(str(cell)))
            
    header_str = "| " + " | ".join(str(h).ljust(w) for h, w in zip(headers, col_widths)) + " |"
    sep_str = "|" + "+".join("-" * (w + 2) for w in col_widths) + "|"
    
    row_strs = []
    for row in rows:
        row_strs.append("| " + " | ".join(str(cell).ljust(w) for cell, w in zip(row, col_widths)) + " |")
        
    return "\n".join([header_str, sep_str] + row_strs) + "\n"

# ==========================================
# 1. Lógica del Autómata 
# ==========================================
class Automaton:
    def __init__(self, alphabet, states, initial_state, final_states, transitions):
        self.alphabet = set(alphabet)
        self.states = set(states)
        self.initial_state = initial_state
        self.final_states = set(final_states)
        self.transitions = transitions

class NFAToDFAConverter:
    @staticmethod
    def get_lambda_closure(states, transitions):
        closure = set(states)
        stack = list(states)
        while stack:
            state = stack.pop()
            lambda_transitions = transitions.get(state, {}).get("lambda", [])
            for next_state in lambda_transitions:
                if next_state not in closure:
                    closure.add(next_state)
                    stack.append(next_state)
        return frozenset(closure)

    @staticmethod
    def convert(nfa: Automaton):
        logs = ["=== PASO 1: CONVERSIÓN AFND A AFD (PASO A PASO) ===\n"]
        dfa_states = set()
        dfa_transitions = {}
        dfa_final_states = set()
        
        logs.append("1. Tabla de Transiciones del Autómata Original (AFND):")
        
        all_symbols = sorted(list(nfa.alphabet))
        if "lambda" in all_symbols:
            all_symbols.remove("lambda")
            all_symbols.append("lambda")
            
        orig_headers = ["Estado"] + [f"δ({sym})" for sym in all_symbols] + ["Final?"]
        orig_rows = []
        for s in sorted(nfa.states):
            row = [s]
            for sym in all_symbols:
                dests = nfa.transitions.get(s, {}).get(sym, [])
                row.append("{" + ", ".join(sorted(dests)) + "}" if dests else "-")
            row.append("Sí" if s in nfa.final_states else "No")
            orig_rows.append(row)
            
        logs.append(format_table(orig_headers, orig_rows))
        
        initial_closure = NFAToDFAConverter.get_lambda_closure([nfa.initial_state], nfa.transitions)
        unprocessed_states = deque([initial_closure])
        processed_states = set()
        
        state_name_map = {}
        state_counter = 0
        
        def get_state_name(state_frozenset):
            nonlocal state_counter
            if state_frozenset not in state_name_map:
                state_name_map[state_frozenset] = f"S{state_counter}"
                state_counter += 1
            return state_name_map[state_frozenset]

        dfa_initial_state = get_state_name(initial_closure)
        valid_alphabet = sorted([s for s in nfa.alphabet if s != "lambda"])

        trans_headers = ["Estado AFD", "Subconjunto AFND"] + [f"δ({sym})" for sym in valid_alphabet] + ["Final?"]
        cumulative_rows = []

        logs.append("2. Construcción de Subconjuntos iterativa:")
        iteration = 1

        while unprocessed_states:
            current_macro = unprocessed_states.popleft()
            if current_macro in processed_states: continue
                
            processed_states.add(current_macro)
            current_name = get_state_name(current_macro)
            dfa_transitions[current_name] = {}
            
            is_final = any(s in nfa.final_states for s in current_macro)
            if is_final: dfa_final_states.add(current_name)
            
            row = [current_name, "{" + ", ".join(sorted(current_macro)) + "}"]
            new_discovered = []
            
            for symbol in valid_alphabet:
                next_macro = set()
                for state in current_macro:
                    next_macro.update(nfa.transitions.get(state, {}).get(symbol, []))
                
                if next_macro:
                    next_closure = NFAToDFAConverter.get_lambda_closure(next_macro, nfa.transitions)
                    next_name = get_state_name(next_closure)
                    dfa_transitions[current_name][symbol] = [next_name]
                    
                    row.append(f"{next_name} ({"{" + ', '.join(sorted(next_closure)) + "}"})")
                    
                    if next_closure not in processed_states and next_closure not in unprocessed_states:
                        unprocessed_states.append(next_closure)
                        new_discovered.append(next_name)
                else:
                    row.append("-")
            
            row.append("Sí" if is_final else "No")
            cumulative_rows.append(row)

            logs.append(f"\n--- Iteración {iteration} ---")
            logs.append(format_table(trans_headers, [row]))
            if new_discovered:
                logs.append(f"-> Nuevos estados descubiertos agregados a la cola: {', '.join(new_discovered)}")
            else:
                logs.append("-> No se descubrieron estados nuevos.")
            
            iteration += 1

        logs.append("\n3. Tabla de Transiciones del AFD Final Alcanzable:")
        logs.append(format_table(trans_headers, cumulative_rows))

        dfa = Automaton(
            alphabet=valid_alphabet,
            states=list(state_name_map.values()),
            initial_state=dfa_initial_state,
            final_states=list(dfa_final_states),
            transitions=dfa_transitions
        )
        return dfa, "\n".join(logs)

class MooreMinimizer:
    @staticmethod
    def minimize(dfa: Automaton):
        logs = ["\n=== PASO 2: MINIMIZACIÓN DE AFD (MÉTODO DE MOORE) ===\n"]
        alphabet = sorted(list(dfa.alphabet))
        states = list(dfa.states)
        transitions = dfa.transitions

        trap_state = "Trap"
        needs_trap = False
        for s in states:
            for a in alphabet:
                if a not in transitions.get(s, {}) or not transitions[s][a]:
                    if s not in transitions: transitions[s] = {}
                    transitions[s][a] = [trap_state]
                    needs_trap = True
        
        if needs_trap:
            states.append(trap_state)
            transitions[trap_state] = {a: [trap_state] for a in alphabet}
            logs.append("Se agregó un estado sumidero (Trap) para completar el AFD.\n")

        classes = {}
        for s in states:
            classes[s] = "G1" if s in dfa.final_states else "G0"

        iteration = 0
        while True:
            logs.append(f"Iteración {iteration} de Moore:")
            headers = ["Estado", "Final?", "Clase P(k)"] + [f"δ({sym})" for sym in alphabet] + ["Firma", "Clase P(k+1)"]
            rows = []
            
            new_classes = {}
            signatures = {}
            next_class_id = 0
            
            for s in sorted(states):
                current_class = classes[s]
                dest_classes = []
                dest_states_str = []
                
                for a in alphabet:
                    dest = transitions[s][a][0]
                    dest_classes.append(classes[dest])
                    dest_states_str.append(f"{dest} ({classes[dest]})")
                
                signature = (current_class, tuple(dest_classes))
                
                if signature not in signatures:
                    signatures[signature] = f"C{next_class_id}"
                    next_class_id += 1
                
                new_class = signatures[signature]
                new_classes[s] = new_class
                
                is_final = "Sí" if s in dfa.final_states else "No"
                row = [s, is_final, current_class] + dest_states_str + [str(signature), new_class]
                rows.append(row)
                
            logs.append(format_table(headers, rows))
            
            if len(set(new_classes.values())) == len(set(classes.values())):
                classes = new_classes
                logs.append("Las clases de equivalencia ya no cambian. Fin de minimización.\n")
                break
                
            classes = new_classes
            iteration += 1

        min_state_map = classes
        min_states = sorted(list(set(classes.values())))
        min_initial = min_state_map[dfa.initial_state]
        min_final_states = set(min_state_map[s] for s in dfa.final_states)
        
        min_transitions = {}
        for s in states:
            m_state = min_state_map[s]
            if m_state not in min_transitions:
                min_transitions[m_state] = {}
                for a in alphabet:
                    dest = transitions[s][a][0]
                    min_transitions[m_state][a] = [min_state_map[dest]]

        reachable = set([min_initial])
        stack = [min_initial]
        while stack:
            curr = stack.pop()
            for a in alphabet:
                dest = min_transitions[curr][a][0]
                if dest not in reachable:
                    reachable.add(dest)
                    stack.append(dest)

        clean_transitions = {}
        for s in reachable:
            clean_transitions[s] = {}
            for a in alphabet:
                dest = min_transitions[s][a][0]
                if dest in reachable:
                    clean_transitions[s][a] = [dest]

        min_dfa = Automaton(
            alphabet=alphabet,
            states=list(reachable),
            initial_state=min_initial,
            final_states=list(min_final_states.intersection(reachable)),
            transitions=clean_transitions
        )
        return min_dfa, "\n".join(logs)

# ==========================================
# 2. Generador de Grafos Visuales
# ==========================================
class GraphRenderer:
    @staticmethod
    def render(automaton, filename, title):
        dot = Digraph(comment=title)
        dot.attr(rankdir='LR', size='5,5')
        dot.node('fake', shape='none', label='')
        dot.edge('fake', automaton.initial_state)

        for state in automaton.states:
            shape = 'doublecircle' if state in automaton.final_states else 'circle'
            dot.node(state, shape=shape)

        for state, trans in automaton.transitions.items():
            for symbol, targets in trans.items():
                for target in targets:
                    dot.edge(state, target, label=symbol)

        dot.render(filename, format='png', cleanup=True)
        return f"{filename}.png"

# ==========================================
# 3. Interfaz Gráfica (Tkinter)
# ==========================================
class AutomataApp:
    def __init__(self, root):
        self.root = root
        self.root.title("TP Integrador 1 - Autómatas")
        self.root.geometry("1200x750")

        top_frame = tk.Frame(root)
        top_frame.pack(side=tk.TOP, fill=tk.X, padx=10, pady=10)

        self.btn_load = tk.Button(top_frame, text="Importar JSON", command=self.load_json, font=("Arial", 12, "bold"))
        self.btn_load.pack(side=tk.LEFT)

        center_frame = tk.Frame(root)
        center_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        self.log_text = scrolledtext.ScrolledText(center_frame, width=75, font=("Consolas", 9))
        self.log_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.img_frame = tk.Frame(center_frame, width=400)
        self.img_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=10)
        
        self.lbl_img_original = tk.Label(self.img_frame, text="AFND Original / AFD")
        self.lbl_img_original.pack()
        
        self.lbl_img_min = tk.Label(self.img_frame, text="AFD Mínimo")
        self.lbl_img_min.pack()

    def load_json(self):
        filepath = filedialog.askopenfilename(filetypes=[("JSON Files", "*.json")])
        if not filepath: return
        
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
            nfa = Automaton(
                alphabet=data['alfabeto'], states=data['estados'],
                initial_state=data['estado_inicial'], final_states=data['estados_finales'],
                transitions=data['transiciones']
            )

            dfa, dfa_logs = NFAToDFAConverter.convert(nfa)
            min_dfa, min_logs = MooreMinimizer.minimize(dfa)
            
            self.log_text.delete('1.0', tk.END)
            self.log_text.insert(tk.END, dfa_logs + "\n" + min_logs)

            GraphRenderer.render(nfa, "nfa_graph", "AFND Original")
            GraphRenderer.render(min_dfa, "min_dfa_graph", "AFD Mínimo")

            self.display_images("nfa_graph.png", "min_dfa_graph.png")
            messagebox.showinfo("Éxito", "Autómata procesado exitosamente.")
            
        except Exception as e:
            messagebox.showerror("Error", f"Ocurrió un error:\n{str(e)}")

    def display_images(self, img1_path, img2_path):
        img1 = Image.open(img1_path)
        img1.thumbnail((400, 300), Image.Resampling.LANCZOS)
        photo1 = ImageTk.PhotoImage(img1)
        self.lbl_img_original.config(image=photo1, text="")
        self.lbl_img_original.image = photo1 

        img2 = Image.open(img2_path)
        img2.thumbnail((400, 300), Image.Resampling.LANCZOS)
        photo2 = ImageTk.PhotoImage(img2)
        self.lbl_img_min.config(image=photo2, text="")
        self.lbl_img_min.image = photo2 

if __name__ == "__main__":
    root = tk.Tk()
    app = AutomataApp(root)
    root.mainloop()