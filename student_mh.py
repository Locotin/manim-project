from manim import *
import random


class MetropolisHastingsStudent(Scene):
    SUBSCRIPT_MAP = str.maketrans("0123456789", "₀₁₂₃₄₅₆₇₈₉")
    NODE_LABELS = {
        "D": "Dificultad",
        "I": "Inteligencia",
        "G": "Nota",
        "S": "Saber",
        "L": "Carta",
    }

    def construct(self):
        self.rng = random.Random(42)
        self.setup_model()

        state = {"D": "d0", "I": "i1", "G": "g2", "S": "s1", "L": "l0"}

        network_group = self.draw_network(state)
        self.play(FadeIn(network_group), run_time=0.8)

        title = Text("Metropolis-Hastings en Student Network", font_size=30)
        title.to_edge(UP)
        self.play(Write(title), run_time=0.6)

        cpt_panel = self.create_cpt_panel()
        self.play(FadeIn(cpt_panel), run_time=0.7)
        self.wait(0.5)

        evidence_text = Text(
            f"Evidencia fija: {self.node_label('S')}={self.fmt_state('s1')}, "
            f"{self.node_label('L')}={self.fmt_state('l0')}",
            font_size=20,
            color=GRAY_A,
        )
        self.state_text = Text(self.state_to_string(state), font_size=22)
        evidence_panel = VGroup(evidence_text, self.state_text)
        evidence_panel.arrange(DOWN, aligned_edge=LEFT, buff=0.1)
        evidence_panel.to_corner(DL, buff=0.6)
        self.play(FadeIn(evidence_panel, shift=UP * 0.08), run_time=0.45)

        self.accept_text = Text("Aceptadas: 0/0 (0.000)", font_size=21, color=YELLOW)
        self.accept_text.to_corner(UL, buff=0.6).shift(DOWN * 0.75)
        self.play(FadeIn(self.accept_text), run_time=0.35)

        calc_line = None
        accepted_count = 0
        order = ["D", "I", "G", "S", "L", "D", "I", "G"]
        u_values = [0.37, 0.82, 0.11, 0.65, 0.49, 0.93, 0.27, 0.58]

        for step, node in enumerate(order, start=1):
            self.highlight_markov_blanket(node)
            self.highlight_cpt_tables(node)

            old_val = state[node]
            proposal_state, qf, qb = self.propose(state, node)
            new_val = proposal_state[node]

            p_x = self.joint_prob(state)
            p_xp = self.joint_prob(proposal_state)
            alpha = self.acceptance_alpha(p_x, p_xp, qf, qb)
            u = u_values[step - 1]
            accepted = u <= alpha

            calc_steps = self.build_calc_steps(step, node, old_val, new_val, p_x, p_xp, alpha, u, accepted)
            calc_line = self.show_calc_steps(calc_line, calc_steps)

            if accepted:
                accepted_count += 1
                state[node] = new_val
                self.update_node_value(node, new_val)
                stamp = Text("ACCEPT", font_size=56, color=GREEN_C, weight=BOLD)
            else:
                stamp = Text("REJECT", font_size=56, color=RED_C, weight=BOLD)

            stamp.move_to(ORIGIN + UP * 0.45)
            self.play(FadeIn(stamp, scale=0.7), run_time=0.2)
            self.wait(0.2)
            self.play(FadeOut(stamp, scale=1.1), run_time=0.2)

            new_state_text = Text(self.state_to_string(state), font_size=22)
            new_state_text.move_to(self.state_text)
            self.play(ReplacementTransform(self.state_text, new_state_text), run_time=0.25)
            self.state_text = new_state_text

            rate = accepted_count / step
            new_accept_text = Text(
                f"Aceptadas: {accepted_count}/{step} ({rate:.3f})",
                font_size=21,
                color=YELLOW,
            )
            new_accept_text.move_to(self.accept_text)
            self.play(ReplacementTransform(self.accept_text, new_accept_text), run_time=0.25)
            self.accept_text = new_accept_text

            self.wait(0.25)
            self.reset_highlights()

        self.wait(1.0)

    def setup_model(self):
        self.states = {
            "D": ["d0", "d1"],
            "I": ["i0", "i1"],
            "G": ["g1", "g2", "g3"],
            "S": ["s0", "s1"],
            "L": ["l0", "l1"],
        }

        self.p_d = {"d0": 0.6, "d1": 0.4}
        self.p_i = {"i0": 0.7, "i1": 0.3}
        self.p_g = {
            ("i0", "d0"): [0.3, 0.4, 0.3],
            ("i0", "d1"): [0.05, 0.25, 0.7],
            ("i1", "d0"): [0.9, 0.08, 0.02],
            ("i1", "d1"): [0.5, 0.3, 0.2],
        }
        self.p_s = {"i0": [0.95, 0.05], "i1": [0.2, 0.8]}
        self.p_l = {"g1": [0.1, 0.9], "g2": [0.4, 0.6], "g3": [0.99, 0.01]}

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

    def joint_prob(self, state):
        factors = self.local_factors(state)
        out = 1.0
        for value in factors.values():
            out *= value
        return out

    def local_factors(self, state):
        d = state["D"]
        i = state["I"]
        g = state["G"]
        s = state["S"]
        l = state["L"]
        return {
            "P(D)": self.p_d[d],
            "P(I)": self.p_i[i],
            "P(G|D,I)": self.p_g[(i, d)][self.states["G"].index(g)],
            "P(S|I)": self.p_s[i][self.states["S"].index(s)],
            "P(L|G)": self.p_l[g][self.states["L"].index(l)],
        }

    def propose(self, state, var):
        state_prime = dict(state)
        choices = [v for v in self.states[var] if v != state[var]]
        state_prime[var] = self.rng.choice(choices)
        q_forward = 1.0 / len(choices)
        q_backward = q_forward
        return state_prime, q_forward, q_backward

    def acceptance_alpha(self, p, pprime, qf, qb):
        if p <= 0:
            return 1.0
        return min(1.0, (pprime * qb) / (p * qf))

    def draw_network(self, state):
        positions = {
            "D": LEFT * 4.2 + UP * 1.8,
            "I": LEFT * 1.6 + UP * 1.8,
            "G": LEFT * 2.9 + UP * 0.1,
            "S": LEFT * 0.3 + UP * 0.1,
            "L": LEFT * 2.9 + DOWN * 1.6,
        }

        group = VGroup()
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
            if node in {"S", "L"}:
                observed = Text("obs", font_size=14, color=GRAY_A)
                observed.next_to(circle, UP + RIGHT, buff=0.03)
                group.add(observed)

        for src, dst in [("D", "G"), ("I", "G"), ("I", "S"), ("G", "L")]:
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
        self.play(
            *[
                circle.animate.set_stroke(YELLOW, width=5)
                if n == node
                else circle.animate.set_stroke(BLUE, width=4)
                if n in blanket
                else circle.animate.set_stroke(WHITE, width=2)
                for n, circle in self.node_circles.items()
            ],
            run_time=0.25,
        )

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
            self.play(FadeOut(self.cpt_links), run_time=0.15)
            self.cpt_links = VGroup()

    def build_calc_steps(self, step, node, old_val, new_val, p_x, p_xp, alpha, u, accepted):
        decision = "ACCEPT" if accepted else "REJECT"
        return [
            f"Paso {step}: Propose {self.node_label(node)}: "
            f"{self.fmt_state(old_val)} -> {self.fmt_state(new_val)}",
            f"P(x) = {p_x:.8f}",
            f"P(x') = {p_xp:.8f}",
            f"alpha = min(1, P(x')/P(x)) = {alpha:.4f}",
            f"u = {u:.2f}  =>  {decision}",
        ]

    def show_calc_steps(self, previous_line, steps):
        line = previous_line
        for txt in steps:
            new_line = Text(txt, font_size=26)
            new_line.to_edge(DOWN, buff=0.15).shift(LEFT * 1.9)
            if new_line.width > 9.0:
                new_line.scale_to_fit_width(9.0)

            if line is None:
                self.play(FadeIn(new_line), run_time=0.65)
            else:
                self.play(ReplacementTransform(line, new_line), run_time=0.85)
            line = new_line
            self.wait(0.65)
        return line

    def update_node_value(self, node, value):
        new_text = Text(self.fmt_state(value), font_size=22)
        new_text.move_to(self.node_value_texts[node].get_center())
        self.play(ReplacementTransform(self.node_value_texts[node], new_text), run_time=0.25)
        self.node_value_texts[node] = new_text

    def highlight_cpt_tables(self, node):
        tables_by_node = {
            "D": [self.prob_label("D"), self.cond_label("G", ["I", "D"])],
            "I": [self.prob_label("I"), self.cond_label("G", ["I", "D"]), self.cond_label("S", ["I"])],
            "G": [self.cond_label("G", ["I", "D"]), self.cond_label("L", ["G"])],
            "S": [self.cond_label("S", ["I"])],
            "L": [self.cond_label("L", ["G"])],
        }
        active = tables_by_node[node]

        self.play(
            *[
                card["box"].animate.set_stroke(YELLOW, width=3.2)
                if name in active
                else card["box"].animate.set_stroke(GRAY_B, width=1.5)
                for name, card in self.cpt_cards.items()
            ],
            run_time=0.25,
        )

        if len(self.cpt_links) > 0:
            self.play(FadeOut(self.cpt_links), run_time=0.15)
            self.cpt_links = VGroup()

        origin = self.node_circles[node].get_right() + RIGHT * 0.05
        links = VGroup()
        for table_name in active:
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

        self.play(*[Create(link) for link in links], run_time=0.3)
        self.cpt_links = links

    def create_cpt_panel(self):
        panel = VGroup()
        title = Text("Tablas de probabilidad", font_size=22)

        cards_data = [
            (self.prob_label("D"), [f"{self.fmt_state('d0')}: 0.60", f"{self.fmt_state('d1')}: 0.40"]),
            (self.prob_label("I"), [f"{self.fmt_state('i0')}: 0.70", f"{self.fmt_state('i1')}: 0.30"]),
            (
                self.cond_label("G", ["I", "D"]),
                [
                    f"{self.fmt_state('i0')},{self.fmt_state('d0')}: [0.30,0.40,0.30]",
                    f"{self.fmt_state('i0')},{self.fmt_state('d1')}: [0.05,0.25,0.70]",
                    f"{self.fmt_state('i1')},{self.fmt_state('d0')}: [0.90,0.08,0.02]",
                    f"{self.fmt_state('i1')},{self.fmt_state('d1')}: [0.50,0.30,0.20]",
                ],
            ),
            (
                self.cond_label("S", ["I"]),
                [f"{self.fmt_state('i0')}: [0.95,0.05]", f"{self.fmt_state('i1')}: [0.20,0.80]"],
            ),
            (
                self.cond_label("L", ["G"]),
                [
                    f"{self.fmt_state('g1')}: [0.10,0.90]",
                    f"{self.fmt_state('g2')}: [0.40,0.60]",
                    f"{self.fmt_state('g3')}: [0.99,0.01]",
                ],
            ),
        ]

        cards_group = VGroup()
        for name, rows in cards_data:
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

        full = VGroup(title, cards_group)
        max_height = config.frame_height - 1.0
        if full.height > max_height:
            full.scale_to_fit_height(max_height)

        full.move_to(RIGHT * 4.45 + DOWN * 0.35)
        panel.add(full)
        return panel

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

    def make_factorization_formula(self):
        return Text(
            f"P({self.node_label('D')},{self.node_label('I')},{self.node_label('G')},"
            f"{self.node_label('S')},{self.node_label('L')})="
            f"{self.prob_label('D')}{self.prob_label('I')}"
            f"{self.cond_label('G', ['D','I'])}{self.cond_label('S', ['I'])}"
            f"{self.cond_label('L', ['G'])}",
            font_size=22,
        )
