from manim import *


class GibbsStudent(Scene):
    def construct(self):
        # State spaces
        self.states = {
            "D": ["d0", "d1"],
            "I": ["i0", "i1"],
            "G": ["g1", "g2", "g3"],
            "S": ["s0", "s1"],
            "L": ["l0", "l1"],
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
            "g1": [0.1, 0.9],
            "g2": [0.4, 0.6],
            "g3": [0.99, 0.01],
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
            "G": "g2",
            "S": "s1",
            "L": "l0",
        }

        network_group = self.draw_network(state)
        self.play(FadeIn(network_group), run_time=0.8)

        title = Text("Student Network: estructura y CPTs", font_size=30)
        title.to_edge(UP)
        self.play(Write(title), run_time=0.6)

        cpt_panel = self.create_cpt_panel()
        self.play(FadeIn(cpt_panel), run_time=0.7)
        self.wait(0.8)

        infer_title = Text("Gibbs Sampling con evidencia", font_size=30)
        infer_title.move_to(title)
        self.play(ReplacementTransform(title, infer_title), run_time=0.55)
        title = infer_title

        evidence_text = Text("Evidencia fija: S=s1, L=l0", font_size=20, color=GRAY_A)
        self.state_text = Text(self.state_to_string(state), font_size=22)
        evidence_panel = VGroup(evidence_text, self.state_text)
        evidence_panel.arrange(DOWN, aligned_edge=LEFT, buff=0.1)
        evidence_panel.move_to(LEFT * 4.25 + DOWN * 2.75)
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

            new_state_text = Text(self.state_to_string(state), font_size=22)
            new_state_text.move_to(self.state_text)
            self.play(ReplacementTransform(self.state_text, new_state_text), run_time=0.35)
            self.state_text = new_state_text

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

            var_text = Text(node, font_size=28, weight=BOLD)
            var_text.move_to(pos + UP * 0.12)

            value_text = Text(state[node], font_size=22)
            value_text.move_to(pos + DOWN * 0.18)

            self.node_circles[node] = circle
            self.node_value_texts[node] = value_text

            group.add(circle, var_text, value_text)
            if node in self.evidence_nodes:
                observed = Text("obs", font_size=14, color=GRAY_A)
                observed.next_to(circle, UP, buff=0.03)
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
            query = "P(D | I, G)"
            factors = "P(D) * P(G | I, D)"
            i_val = state["I"]
            g_val = state["G"]
            for d_val in candidate_states:
                f1 = self.p_d[d_val]
                f2 = self.p_g[(i_val, d_val)][self.states["G"].index(g_val)]
                u = f1 * f2
                rows.append(f"{d_val}: {f1:.3f} * {f2:.3f} = {u:.5f}")
                unnorm.append(u)

        elif node == "I":
            query = "P(I | D, G, S)"
            factors = "P(I) * P(G | I, D) * P(S | I)"
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
                rows.append(f"{i_val}: {f1:.3f} * {f2:.3f} * {f3:.3f} = {u:.5f}")
                unnorm.append(u)

        elif node == "G":
            query = "P(G | D, I, L)"
            factors = "P(G | I, D) * P(L | G)"
            d_val = state["D"]
            i_val = state["I"]
            l_val = state["L"]
            l_idx = self.states["L"].index(l_val)
            for g_val in candidate_states:
                f1 = self.p_g[(i_val, d_val)][self.states["G"].index(g_val)]
                f2 = self.p_l[g_val][l_idx]
                u = f1 * f2
                rows.append(f"{g_val}: {f1:.3f} * {f2:.3f} = {u:.5f}")
                unnorm.append(u)

        elif node == "S":
            query = "P(S | I)"
            factors = "P(S | I)"
            i_val = state["I"]
            for s_val in candidate_states:
                u = self.p_s[i_val][self.states["S"].index(s_val)]
                rows.append(f"{s_val}: {u:.3f}")
                unnorm.append(u)

        else:  # node == "L"
            query = "P(L | G)"
            factors = "P(L | G)"
            g_val = state["G"]
            for l_val in candidate_states:
                u = self.p_l[g_val][self.states["L"].index(l_val)]
                rows.append(f"{l_val}: {u:.3f}")
                unnorm.append(u)

        z = sum(unnorm)
        norm = [u / z if z > 0 else 0.0 for u in unnorm]

        # Deterministic update: choose MAP state
        max_idx = max(range(len(norm)), key=lambda idx: norm[idx])
        chosen = candidate_states[max_idx]

        dist_str = ", ".join(
            [f"{candidate_states[k]}={norm[k]:.3f}" for k in range(len(candidate_states))]
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
            f"Actualizacion: {cond['node']} {old_state} -> {cond['chosen']}"
            if cond["chosen"] != old_state
            else f"Actualizacion: {cond['node']} sin cambio ({cond['chosen']})"
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
        calc_text.to_edge(DOWN, buff=0.38).shift(LEFT * 2.2)
        max_width = 8.6
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
        new_text = Text(new_state, font_size=22)
        new_text.move_to(self.node_value_texts[node].get_center())
        self.play(ReplacementTransform(self.node_value_texts[node], new_text), run_time=0.2)
        self.node_value_texts[node] = new_text

    def show_node_update_feedback(self, node, old_state, new_state):
        changed = new_state != old_state
        msg = (
            Text(f"{node}: {old_state} -> {new_state}", font_size=18, color=GREEN_C)
            if changed
            else Text(f"{node}: sin cambio", font_size=18, color=GRAY_A)
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
            ("P(D)", ["d0: 0.60", "d1: 0.40"]),
            ("P(I)", ["i0: 0.70", "i1: 0.30"]),
            (
                "P(G|I,D)",
                [
                    "i0,d0: [0.30, 0.40, 0.30]",
                    "i0,d1: [0.05, 0.25, 0.70]",
                    "i1,d0: [0.90, 0.08, 0.02]",
                    "i1,d1: [0.50, 0.30, 0.20]",
                ],
            ),
            ("P(S|I)", ["i0: [0.95, 0.05]", "i1: [0.20, 0.80]"]),
            ("P(L|G)", ["g1: [0.10, 0.90]", "g2: [0.40, 0.60]", "g3: [0.99, 0.01]"]),
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
            "D": ["P(D)", "P(G|I,D)"],
            "I": ["P(I)", "P(G|I,D)", "P(S|I)"],
            "G": ["P(G|I,D)", "P(L|G)"],
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
            f"D={state['D']}, I={state['I']}, G={state['G']}, "
            f"S={state['S']}, L={state['L']}"
        )
