from manim import *


class GibbsStudent(Scene):
    SUBSCRIPT_MAP = str.maketrans("0123456789", "₀₁₂₃₄₅₆₇₈₉")
    NODE_LABELS = {
        "D": "Dificultad",
        "I": "Inteligencia",
        "G": "Nota",
        "S": "Saber",
        "L": "Carta",
    }

    def construct(self):
        # State spaces
        self.states = {
            "D": ["d0", "d1"],
            "I": ["i0", "i1"],
            "G": ["n1", "n2", "n3"],
            "S": ["s0", "s1"],
            "L": ["c0", "c1"],
        }

        # Priors and CPTs
        self.p_d = {"d0": 0.6, "d1": 0.4}
        self.p_i = {"i0": 0.7, "i1": 0.3}
        self.p_g = {
            ("i0", "d0"): [0.3, 0.4, 0.3],
            ("i0", "d1"): [0.05, 0.25, 0.7],
            ("i1", "d0"): [0.9, 0.08, 0.02],
            ("i1", "d1"): [0.5, 0.3, 0.2],
        }
        self.p_s = {
            "i0": [0.95, 0.05],
            "i1": [0.2, 0.8],
        }
        self.p_l = {
            "n1": [0.1, 0.9],
            "n2": [0.4, 0.6],
            "n3": [0.99, 0.01],
        }

        self.markov_blankets = {
            "D": ["I", "G"],
            "I": ["D", "G", "S"],
            "G": ["D", "I", "L"],
            "S": ["I"],
            "L": ["G"],
        }

        self.node_colors = {
            "D": TEAL_C,
            "I": ORANGE,
            "G": GREEN_C,
            "S": PURPLE_C,
            "L": RED_C,
        }

        self.node_circles = {}
        self.node_value_texts = {}
        self.cpt_cards = {}
        self.cpt_links = VGroup()
        self.evidence_nodes = {"S", "L"}

        # Initial state (example requested)
        state = {
            "D": "d0",
            "I": "i1",
            "G": "n2",
            "S": "s1",
            "L": "c0",
        }

        network_group = self.draw_network(state)
        self.play(FadeIn(network_group), run_time=0.8)

        title = Text("Estructura y CPTs", font_size=30)
        title.to_edge(UP)
        self.play(Write(title), run_time=0.6)

        cpt_panel = self.create_cpt_panel()
        self.play(FadeIn(cpt_panel), run_time=0.7)
        self.wait(0.8)

        infer_title = Text("Muestreo de Gibbs con evidencia", font_size=30)
        infer_title.move_to(title)
        self.play(ReplacementTransform(title, infer_title), run_time=0.55)
        title = infer_title

        evidence_text = Text(
            f"Evidencia fija: {self.node_label('S')}={self.fmt_state('s1')}, "
            f"{self.node_label('L')}={self.fmt_state('c0')}",
            font_size=22,
            color=GRAY_A,
        )
        evidence_panel = VGroup(evidence_text)
        evidence_panel.arrange(DOWN, aligned_edge=LEFT, buff=0.1)
        evidence_panel.to_corner(DL, buff=0.6).shift(UP * 0.35)
        self.play(FadeIn(evidence_panel, shift=UP * 0.08), run_time=0.45)

        calc_line = None

        # Single Gibbs sweep over latent nodes, with S and L as fixed evidence
        update_order = ["D", "I", "G"]
        step = 1
        for node in update_order:
            self.highlight_markov_blanket(node)
            self.highlight_cpt_tables(node)

            cond = self.compute_conditional(node, state)
            old_state = state[node]
            calc_steps = self.build_calc_steps(step, cond, old_state)
            calc_line = self.show_calc_steps(calc_line, calc_steps)

            chosen_state = cond["chosen"]
            self.update_node_value(node, chosen_state, old_state)
            self.show_node_update_feedback(node, old_state, chosen_state)
            state[node] = chosen_state

            # State text was removed; no replacement needed.

            self.wait(0.45)
            self.reset_highlights()
            step += 1

        self.wait(1.0)

    def draw_network(self, state):
        positions = {
            "D": LEFT * 4.2 + UP * 1.8,
            "I": LEFT * 1.6 + UP * 1.8,
            "G": LEFT * 2.9 + UP * 0.1,
            "S": LEFT * 0.3 + UP * 0.1,
            "L": LEFT * 2.9 + DOWN * 1.6,
        }

        group = VGroup()

        # Nodes with variable name and current state
        for node, pos in positions.items():
            circle = Circle(radius=0.42, stroke_color=WHITE, stroke_width=2)
            circle.set_fill(self.node_colors[node], opacity=0.22)
            circle.move_to(pos)

            var_text = Text(self.node_label(node), font_size=18, weight=BOLD)
            if node == "L":
                var_text.next_to(circle, DOWN, buff=0.08)
            else:
                var_text.next_to(circle, UP, buff=0.08)

            value_text = Text(self.fmt_state(state[node]), font_size=22)
            value_text.move_to(circle.get_center())

            self.node_circles[node] = circle
            self.node_value_texts[node] = value_text

            group.add(circle, var_text, value_text)
            if node in self.evidence_nodes:
                observed = Text("obs", font_size=14, color=GRAY_A)
                observed.next_to(circle, UP + RIGHT, buff=0.03)
                group.add(observed)

        # Directed edges
        edges = [
            ("D", "G"),
            ("I", "G"),
            ("I", "S"),
            ("G", "L"),
        ]

        for src, dst in edges:
            arrow = Arrow(
                self.node_circles[src].get_center(),
                self.node_circles[dst].get_center(),
                buff=0.45,
                stroke_width=3,
                max_tip_length_to_length_ratio=0.18,
            )
            group.add(arrow)

        return group

    def highlight_markov_blanket(self, node):
        blanket = self.markov_blankets[node]
        anims = []

        for n, circle in self.node_circles.items():
            if n == node:
                anims.append(circle.animate.set_stroke(YELLOW, width=5))
            elif n in blanket:
                anims.append(circle.animate.set_stroke(BLUE, width=4))
            else:
                anims.append(circle.animate.set_stroke(WHITE, width=2))

        self.play(*anims, run_time=0.25)

    def reset_highlights(self):
        self.play(
            *[circle.animate.set_stroke(WHITE, width=2) for circle in self.node_circles.values()],
            run_time=0.2,
        )
        if len(self.cpt_cards) > 0:
            self.play(
                *[card["box"].animate.set_stroke(GRAY_B, width=1.5) for card in self.cpt_cards.values()],
                run_time=0.2,
            )
        if len(self.cpt_links) > 0:
            self.play(FadeOut(self.cpt_links), run_time=0.2)
            self.cpt_links = VGroup()

    def compute_conditional(self, node, state):
        # Returns formula strings + unnormalized/normalized values for the active variable
        candidate_states = self.states[node]
        rows = []
        unnorm = []

        if node == "D":
            query = f"{self.cond_label('D', ['I','G'])}"
            factors = f"{self.prob_label('D')} * {self.cond_label('G', ['I','D'])}"
            i_val = state["I"]
            g_val = state["G"]
            for d_val in candidate_states:
                f1 = self.p_d[d_val]
                f2 = self.p_g[(i_val, d_val)][self.states["G"].index(g_val)]
                u = f1 * f2
                rows.append(f"{self.fmt_state(d_val)}: {f1:.3f} * {f2:.3f} = {u:.5f}")
                unnorm.append(u)

        elif node == "I":
            query = f"{self.cond_label('I', ['D','G','S'])}"
            factors = f"{self.prob_label('I')} * {self.cond_label('G', ['I','D'])} * {self.cond_label('S', ['I'])}"
            d_val = state["D"]
            g_val = state["G"]
            s_val = state["S"]
            g_idx = self.states["G"].index(g_val)
            s_idx = self.states["S"].index(s_val)
            for i_val in candidate_states:
                f1 = self.p_i[i_val]
                f2 = self.p_g[(i_val, d_val)][g_idx]
                f3 = self.p_s[i_val][s_idx]
                u = f1 * f2 * f3
                rows.append(f"{self.fmt_state(i_val)}: {f1:.3f} * {f2:.3f} * {f3:.3f} = {u:.5f}")
                unnorm.append(u)

        elif node == "G":
            query = f"{self.cond_label('G', ['D','I','L'])}"
            factors = f"{self.cond_label('G', ['I','D'])} * {self.cond_label('L', ['G'])}"
            d_val = state["D"]
            i_val = state["I"]
            l_val = state["L"]
            l_idx = self.states["L"].index(l_val)
            for g_val in candidate_states:
                f1 = self.p_g[(i_val, d_val)][self.states["G"].index(g_val)]
                f2 = self.p_l[g_val][l_idx]
                u = f1 * f2
                rows.append(f"{self.fmt_state(g_val)}: {f1:.3f} * {f2:.3f} = {u:.5f}")
                unnorm.append(u)

        elif node == "S":
            query = f"{self.cond_label('S', ['I'])}"
            factors = f"{self.cond_label('S', ['I'])}"
            i_val = state["I"]
            for s_val in candidate_states:
                u = self.p_s[i_val][self.states["S"].index(s_val)]
                rows.append(f"{self.fmt_state(s_val)}: {u:.3f}")
                unnorm.append(u)

        else:  # node == "L"
            query = f"{self.cond_label('L', ['G'])}"
            factors = f"{self.cond_label('L', ['G'])}"
            g_val = state["G"]
            for l_val in candidate_states:
                u = self.p_l[g_val][self.states["L"].index(l_val)]
                rows.append(f"{self.fmt_state(l_val)}: {u:.3f}")
                unnorm.append(u)

        z = sum(unnorm)
        norm = [u / z if z > 0 else 0.0 for u in unnorm]

        # Deterministic update: choose MAP state
        max_idx = max(range(len(norm)), key=lambda idx: norm[idx])
        chosen = candidate_states[max_idx]

        dist_str = ", ".join(
            [f"{self.fmt_state(candidate_states[k])}={norm[k]:.3f}" for k in range(len(candidate_states))]
        )

        return {
            "node": node,
            "query": query,
            "factors": factors,
            "rows": rows,
            "z": z,
            "dist_str": dist_str,
            "chosen": chosen,
        }

    def build_calc_steps(self, step, cond, old_state):
        update_msg = (
            f"Actualizacion: {self.node_label(cond['node'])} "
            f"{self.fmt_state(old_state)} -> {self.fmt_state(cond['chosen'])}"
            if cond["chosen"] != old_state
            else f"Actualizacion: {self.node_label(cond['node'])} sin cambio "
                 f"({self.fmt_state(cond['chosen'])})"
        )
        steps = [
            f"Paso {step}: {cond['query']}",
            f"Factores: {cond['factors']}",
        ]
        steps.extend(cond["rows"])
        steps.append(f"Normalizar con Z={cond['z']:.5f}")
        steps.append(f"Distribucion final: {cond['dist_str']}")
        steps.append(update_msg)
        return steps

    def make_calc_text(self, text):
        calc_text = Text(text, font_size=26)
        calc_text.to_edge(DOWN, buff=0.25).shift(LEFT * 2.0)
        max_width = 7.2
        if calc_text.width > max_width:
            calc_text.scale_to_fit_width(max_width)
        return calc_text

    def show_calc_steps(self, previous_line, steps):
        line = previous_line
        for step_text in steps:
            new_line = self.make_calc_text(step_text)
            if line is None:
                self.play(FadeIn(new_line), run_time=0.7)
            else:
                self.play(ReplacementTransform(line, new_line), run_time=0.95)
            line = new_line
            self.wait(0.8)
        return line

    def update_node_value(self, node, new_state, old_state):
        if new_state == old_state:
            return
        new_text = Text(self.fmt_state(new_state), font_size=22)
        new_text.move_to(self.node_value_texts[node].get_center())
        self.play(ReplacementTransform(self.node_value_texts[node], new_text), run_time=0.2)
        self.node_value_texts[node] = new_text

    def show_node_update_feedback(self, node, old_state, new_state):
        changed = new_state != old_state
        msg = (
            Text(
                f"{self.node_label(node)}: {self.fmt_state(old_state)} -> {self.fmt_state(new_state)}",
                font_size=18,
                color=GREEN_C,
            )
            if changed
            else Text(f"{self.node_label(node)}: sin cambio", font_size=18, color=GRAY_A)
        )
        msg.next_to(self.node_circles[node], DOWN, buff=0.12)
        self.play(Indicate(self.node_circles[node], color=GREEN_C if changed else GRAY_A), FadeIn(msg), run_time=0.35)
        self.wait(0.2)
        self.play(FadeOut(msg), run_time=0.2)

    def create_cpt_panel(self):
        panel = VGroup()
        panel.to_edge(RIGHT, buff=0.35).shift(DOWN * 0.45)

        title = Text("Tablas de probabilidad", font_size=22)

        cards_data = [
            (self.prob_label("D"), [f"{self.fmt_state('d0')}: 0.60", f"{self.fmt_state('d1')}: 0.40"]),
            (self.prob_label("I"), [f"{self.fmt_state('i0')}: 0.70", f"{self.fmt_state('i1')}: 0.30"]),
            (
                self.cond_label("G", ["I", "D"]),
                [
                    f"{self.fmt_state('i0')},{self.fmt_state('d0')}: [0.30, 0.40, 0.30]",
                    f"{self.fmt_state('i0')},{self.fmt_state('d1')}: [0.05, 0.25, 0.70]",
                    f"{self.fmt_state('i1')},{self.fmt_state('d0')}: [0.90, 0.08, 0.02]",
                    f"{self.fmt_state('i1')},{self.fmt_state('d1')}: [0.50, 0.30, 0.20]",
                ],
            ),
            (
                self.cond_label("S", ["I"]),
                [f"{self.fmt_state('i0')}: [0.95, 0.05]", f"{self.fmt_state('i1')}: [0.20, 0.80]"],
            ),
            (
                self.cond_label("L", ["G"]),
                [
                    f"{self.fmt_state('n1')}: [0.10, 0.90]",
                    f"{self.fmt_state('n2')}: [0.40, 0.60]",
                    f"{self.fmt_state('n3')}: [0.99, 0.01]",
                ],
            ),
        ]
        cards_group = VGroup()
        for idx, (name, rows) in enumerate(cards_data):
            header = Text(name, font_size=17, weight=BOLD)
            body = VGroup(*[Text(line, font_size=14) for line in rows])
            body.arrange(DOWN, aligned_edge=LEFT, buff=0.05)
            content = VGroup(header, body).arrange(DOWN, aligned_edge=LEFT, buff=0.08)

            box = RoundedRectangle(corner_radius=0.08, width=4.7, height=content.height + 0.24)
            box.set_stroke(GRAY_B, width=1.5)
            box.set_fill(BLACK, opacity=0.1)

            card = VGroup(box, content)
            content.move_to(box.get_center())
            cards_group.add(card)
            self.cpt_cards[name] = {"group": card, "box": box}

        cards_group.arrange(DOWN, aligned_edge=LEFT, buff=0.14)
        cards_group.next_to(title, DOWN, buff=0.14, aligned_edge=LEFT)

        full_block = VGroup(title, cards_group)
        max_height = config.frame_height - 1.0
        if full_block.height > max_height:
            full_block.scale_to_fit_height(max_height)

        full_block.move_to(RIGHT * 4.45 + DOWN * 0.35)
        panel.add(full_block)

        return panel

    def highlight_cpt_tables(self, node):
        tables_by_node = {
            "D": [self.prob_label("D"), self.cond_label("G", ["I", "D"])],
            "I": [self.prob_label("I"), self.cond_label("G", ["I", "D"]), self.cond_label("S", ["I"])],
            "G": [self.cond_label("G", ["I", "D"]), self.cond_label("L", ["G"])],
        }
        active_tables = tables_by_node[node]

        self.play(
            *[
                card["box"].animate.set_stroke(YELLOW, width=3.5)
                if name in active_tables
                else card["box"].animate.set_stroke(GRAY_B, width=1.5)
                for name, card in self.cpt_cards.items()
            ],
            run_time=0.28,
        )

        if len(self.cpt_links) > 0:
            self.play(FadeOut(self.cpt_links), run_time=0.15)
            self.cpt_links = VGroup()

        origin = self.node_circles[node].get_right() + RIGHT * 0.05
        links = VGroup()
        for table_name in active_tables:
            target = self.cpt_cards[table_name]["box"].get_left() + LEFT * 0.02
            link = Arrow(
                origin,
                target,
                buff=0.05,
                stroke_width=2.2,
                color=YELLOW,
                max_tip_length_to_length_ratio=0.2,
            )
            links.add(link)

        self.play(*[Create(link) for link in links], run_time=0.35)
        self.cpt_links = links

    def state_to_string(self, state):
        return (
            f"{self.node_label('D')}={self.fmt_state(state['D'])}, "
            f"{self.node_label('I')}={self.fmt_state(state['I'])}, "
            f"{self.node_label('G')}={self.fmt_state(state['G'])}, "
            f"{self.node_label('S')}={self.fmt_state(state['S'])}, "
            f"{self.node_label('L')}={self.fmt_state(state['L'])}"
        )

    def fmt_state(self, token):
        if len(token) >= 2 and token[0].isalpha() and token[1:].isdigit():
            return token[0] + token[1:].translate(self.SUBSCRIPT_MAP)
        return token

    def node_label(self, node):
        return self.NODE_LABELS.get(node, node)

    def prob_label(self, node):
        return f"P({self.node_label(node)})"

    def cond_label(self, node, parents):
        parents_str = ",".join(self.node_label(p) for p in parents)
        return f"P({self.node_label(node)}|{parents_str})"


class MarkovBlanketStudent(GibbsStudent):
    def construct(self):
        self.markov_blankets = {
            "D": ["I", "G"],
            "I": ["D", "G", "S"],
            "G": ["D", "I", "L"],
            "S": ["I"],
            "L": ["G"],
        }
        self.node_colors = {
            "D": TEAL_C,
            "I": ORANGE,
            "G": GREEN_C,
            "S": PURPLE_C,
            "L": RED_C,
        }
        self.node_circles = {}
        self.node_value_texts = {}
        self.cpt_cards = {}
        self.cpt_links = VGroup()
        self.evidence_nodes = {"S", "L"}

        state = {"D": "d0", "I": "i1", "G": "n2", "S": "s1", "L": "c0"}
        network_group = self.draw_network(state)
        self.play(FadeIn(network_group), run_time=0.7)

        title = Text("Manta de Markov", font_size=32)
        title.to_edge(UP)
        self.play(Write(title), run_time=0.6)

        legend = VGroup(
            Text("Amarillo: nodo activo", font_size=26, color=YELLOW),
            Text("Azul: nodos en su manta de Markov", font_size=26, color=BLUE),
        ).arrange(DOWN, aligned_edge=LEFT, buff=0.07)
        legend.to_corner(UR, buff=0.4).shift(DOWN * 0.8)
        self.play(FadeIn(legend), run_time=0.5)

        mb_text = Text("MB(X) = {...}", font_size=30, color=YELLOW)
        mb_text.to_edge(DOWN, buff=0.35)
        self.play(FadeIn(mb_text), run_time=0.4)
        blanket_outline = VGroup()

        for node in ["D", "I", "G"]:
            self.highlight_markov_blanket(node)
            new_outline = self.create_blanket_outline(self.markov_blankets[node])
            if len(blanket_outline) == 0:
                self.play(Create(new_outline), run_time=0.35)
            else:
                self.play(ReplacementTransform(blanket_outline, new_outline), run_time=0.35)
            blanket_outline = new_outline

            mb_set = ", ".join(self.node_label(n) for n in self.markov_blankets[node])
            new_text = Text(f"MB({self.node_label(node)}) = {{{mb_set}}}", font_size=30, color=YELLOW)
            new_text.move_to(mb_text)
            self.play(ReplacementTransform(mb_text, new_text), run_time=0.4)
            mb_text = new_text
            self.wait(0.7)
            self.reset_highlights()

        self.play(FadeOut(blanket_outline), run_time=0.25)
        self.wait(0.9)

    def create_blanket_outline(self, blanket_nodes):
        outlines = VGroup()
        for node in blanket_nodes:
            ring = Circle(radius=0.62)
            ring.move_to(self.node_circles[node].get_center())
            dashed_ring = DashedVMobject(
                ring,
                num_dashes=24,
                dashed_ratio=0.6,
                color=BLUE,
            )
            dashed_ring.set_stroke(color=BLUE, width=3.2)
            outlines.add(dashed_ring)
        return outlines
