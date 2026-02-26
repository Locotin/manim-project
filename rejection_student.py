from manim import *
import random


class RejectionStudent(Scene):
    SUBSCRIPT_MAP = str.maketrans("0123456789", "₀₁₂₃₄₅₆₇₈₉")
    NODE_LABELS = {
        "D": "Dificultad",
        "I": "Inteligencia",
        "G": "Nota",
        "S": "Saber",
        "L": "Carta",
    }

    def construct(self):
        self.rng = random.Random(11)
        self.setup_model()

        title = Text("Muestreo por rechazo", font_size=32)
        title.to_edge(UP)
        self.play(Write(title), run_time=0.8)

        # Evidence and query
        evidence = {"S": "s1", "L": "c0"}
        query_target = ("I", "i1")

        subtitle = Text(
            f"Evidencia: {self.node_label('S')}={self.fmt_state('s1')}, "
            f"{self.node_label('L')}={self.fmt_state('c0')}  |  "
            f"Consulta: P({self.node_label('I')}={self.fmt_state('i1')} | evidencia)",
            font_size=22,
            color=GRAY_A,
        )
        subtitle.next_to(title, DOWN, buff=0.15)
        self.play(FadeIn(subtitle, shift=DOWN * 0.1), run_time=0.5)

        state = {"D": "d0", "I": "i0", "G": "n1", "S": "s1", "L": "c0"}
        network = self.draw_network(state)
        self.play(FadeIn(network), run_time=0.8)

        self.highlight_evidence_nodes()

        counters = self.create_counter_panel()
        self.play(FadeIn(counters), run_time=0.5)

        sample_line = Text("Muestra 0: --", font_size=22)
        decision_line = Text("Estado: --", font_size=22, color=GRAY_A)
        display_group = VGroup(sample_line, decision_line)
        display_group.arrange(DOWN, aligned_edge=LEFT, buff=0.08)
        display_group.to_edge(DOWN, buff=0.35)
        self.play(FadeIn(display_group), run_time=0.4)

        accepted = 0
        rejected = 0
        hits = 0

        total_samples = 18
        for k in range(1, total_samples + 1):
            sample = self.ancestral_sample()
            self.animate_state_update(sample)

            evidence_ok = sample["S"] == evidence["S"] and sample["L"] == evidence["L"]
            if evidence_ok:
                accepted += 1
                is_hit = sample[query_target[0]] == query_target[1]
                if is_hit:
                    hits += 1

                est = hits / accepted if accepted > 0 else 0.0
                status_text = "ACEPTADA"
                status_color = GREEN_C
            else:
                rejected += 1
                est = hits / accepted if accepted > 0 else 0.0
                status_text = "RECHAZADA"
                status_color = RED_C

            self.highlight_accept_reject(evidence_ok)
            new_sample = Text(
                f"Muestra {k}: {self.sample_state_string(sample)}",
                font_size=22,
            )
            new_sample.move_to(sample_line)
            new_decision = Text(f"Estado: {status_text}", font_size=22, color=status_color)
            new_decision.move_to(decision_line)
            # Re-display the state each sample (fade out/in) to emphasize change.
            self.play(FadeOut(sample_line), FadeOut(decision_line), run_time=0.15)
            self.play(FadeIn(new_sample), FadeIn(new_decision), run_time=0.2)
            sample_line = new_sample
            decision_line = new_decision

            self.update_counters(accepted, rejected, hits, est)
            self.wait(0.35)

        final_text = Text(
            f"Estimacion final: P({self.node_label('I')}={self.fmt_state('i1')} | "
            f"{self.node_label('S')}={self.fmt_state('s1')}, "
            f"{self.node_label('L')}={self.fmt_state('c0')}) "
            f"≈ {hits}/{max(accepted,1)} = {hits / max(accepted,1):.3f}",
            font_size=26,
            color=YELLOW,
        )
        final_text.to_edge(DOWN, buff=0.25)
        self.play(ReplacementTransform(display_group, final_text), run_time=0.5)
        self.wait(1.2)

    def setup_model(self):
        self.states = {
            "D": ["d0", "d1"],
            "I": ["i0", "i1"],
            "G": ["n1", "n2", "n3"],
            "S": ["s0", "s1"],
            "L": ["c0", "c1"],
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
        self.p_l = {"n1": [0.1, 0.9], "n2": [0.4, 0.6], "n3": [0.99, 0.01]}

        self.node_colors = {
            "D": TEAL_C,
            "I": ORANGE,
            "G": GREEN_C,
            "S": PURPLE_C,
            "L": RED_C,
        }
        self.node_positions = {
            "D": LEFT * 4.1 + UP * 1.7,
            "I": LEFT * 1.6 + UP * 1.7,
            "G": LEFT * 2.85 + UP * 0.05,
            "S": LEFT * 0.3 + UP * 0.05,
            "L": LEFT * 2.85 + DOWN * 1.55,
        }

    def draw_network(self, state):
        self.node_circles = {}
        self.node_values = {}
        group = VGroup()

        for node, pos in self.node_positions.items():
            circle = Circle(radius=0.42, stroke_color=WHITE, stroke_width=2)
            circle.set_fill(self.node_colors[node], opacity=0.22)
            circle.move_to(pos)

            label = Text(self.node_label(node), font_size=18, weight=BOLD)
            if node == "L":
                label.next_to(circle, DOWN, buff=0.08)
            else:
                label.next_to(circle, UP, buff=0.08)
            value = Text(self.fmt_state(state[node]), font_size=22).move_to(circle.get_center())

            self.node_circles[node] = circle
            self.node_values[node] = value
            group.add(circle, label, value)

        for src, dst in [("D", "G"), ("I", "G"), ("I", "S"), ("G", "L")]:
            group.add(
                Arrow(
                    self.node_circles[src].get_center(),
                    self.node_circles[dst].get_center(),
                    buff=0.45,
                    stroke_width=3,
                    max_tip_length_to_length_ratio=0.18,
                )
            )

        return group

    def highlight_evidence_nodes(self):
        tag_s = Text("obs", font_size=14, color=GRAY_A).next_to(self.node_circles["S"], UP + RIGHT, buff=0.03)
        tag_l = Text("obs", font_size=14, color=GRAY_A).next_to(self.node_circles["L"], UP + RIGHT, buff=0.03)
        self.play(
            self.node_circles["S"].animate.set_stroke(BLUE, width=4),
            self.node_circles["L"].animate.set_stroke(BLUE, width=4),
            FadeIn(tag_s),
            FadeIn(tag_l),
            run_time=0.4,
        )

    def create_counter_panel(self):
        self.acc_text = Text("Aceptadas: 0", font_size=22, color=GREEN_C)
        self.rej_text = Text("Rechazadas: 0", font_size=22, color=RED_C)
        self.hit_text = Text(
            f"Hits {self.node_label('I')}={self.fmt_state('i1')}: 0",
            font_size=22,
        )
        self.est_text = Text("Estimacion: 0.000", font_size=22, color=YELLOW)

        panel = VGroup(self.acc_text, self.rej_text, self.hit_text, self.est_text)
        panel.arrange(DOWN, aligned_edge=LEFT, buff=0.08)
        # Lower the stats panel to avoid overlapping the title/evidence line.
        panel.to_corner(UR, buff=0.45).shift(DOWN * 1.6)
        return panel

    def update_counters(self, accepted, rejected, hits, est):
        new_acc = Text(f"Aceptadas: {accepted}", font_size=22, color=GREEN_C).move_to(self.acc_text)
        new_rej = Text(f"Rechazadas: {rejected}", font_size=22, color=RED_C).move_to(self.rej_text)
        new_hit = Text(
            f"Hits {self.node_label('I')}={self.fmt_state('i1')}: {hits}",
            font_size=22,
        ).move_to(self.hit_text)
        new_est = Text(f"Estimacion: {est:.3f}", font_size=22, color=YELLOW).move_to(self.est_text)

        self.play(
            ReplacementTransform(self.acc_text, new_acc),
            ReplacementTransform(self.rej_text, new_rej),
            ReplacementTransform(self.hit_text, new_hit),
            ReplacementTransform(self.est_text, new_est),
            run_time=0.22,
        )
        self.acc_text, self.rej_text, self.hit_text, self.est_text = new_acc, new_rej, new_hit, new_est

    def animate_state_update(self, sample):
        anims = []
        for node in ["D", "I", "G", "S", "L"]:
            new_text = Text(self.fmt_state(sample[node]), font_size=22)
            new_text.move_to(self.node_values[node].get_center())
            anims.append(ReplacementTransform(self.node_values[node], new_text))
            self.node_values[node] = new_text
        self.play(*anims, run_time=0.35)

    def highlight_accept_reject(self, accepted):
        color = GREEN_C if accepted else RED_C
        self.play(
            *[self.node_circles[n].animate.set_stroke(color if n in {"S", "L"} else WHITE, width=4 if n in {"S", "L"} else 2)
              for n in self.node_circles],
            run_time=0.22,
        )
        self.play(
            self.node_circles["S"].animate.set_stroke(BLUE, width=4),
            self.node_circles["L"].animate.set_stroke(BLUE, width=4),
            run_time=0.18,
        )

    def sample_cat(self, labels, probs):
        u = self.rng.random()
        acc = 0.0
        for label, p in zip(labels, probs):
            acc += p
            if u <= acc:
                return label
        return labels[-1]

    def ancestral_sample(self):
        d = self.sample_cat(["d0", "d1"], [self.p_d["d0"], self.p_d["d1"]])
        i = self.sample_cat(["i0", "i1"], [self.p_i["i0"], self.p_i["i1"]])
        g = self.sample_cat(["n1", "n2", "n3"], self.p_g[(i, d)])
        s = self.sample_cat(["s0", "s1"], self.p_s[i])
        l = self.sample_cat(["c0", "c1"], self.p_l[g])
        return {"D": d, "I": i, "G": g, "S": s, "L": l}

    def fmt_state(self, token):
        if len(token) >= 2 and token[0].isalpha() and token[1:].isdigit():
            return token[0] + token[1:].translate(self.SUBSCRIPT_MAP)
        return token

    def node_label(self, node):
        return self.NODE_LABELS.get(node, node)

    def sample_state_string(self, sample):
        return (
            f"{self.node_label('D')}={self.fmt_state(sample['D'])}, "
            f"{self.node_label('I')}={self.fmt_state(sample['I'])}, "
            f"{self.node_label('G')}={self.fmt_state(sample['G'])}, "
            f"{self.node_label('S')}={self.fmt_state(sample['S'])}, "
            f"{self.node_label('L')}={self.fmt_state(sample['L'])}"
        )


class LikelihoodWeightingStudent(RejectionStudent):
    def construct(self):
        self.rng = random.Random(17)
        self.setup_model()

        title = Text("Ponderado en Verosimilitud", font_size=32)
        title.to_edge(UP)
        self.play(Write(title), run_time=0.8)

        subtitle = Text(
            f"Evidencia fija: {self.node_label('S')}={self.fmt_state('s1')}, "
            f"{self.node_label('L')}={self.fmt_state('c0')}  |  "
            f"Consulta: P({self.node_label('I')}={self.fmt_state('i1')} | evidencia)",
            font_size=22,
            color=GRAY_A,
        )
        subtitle.next_to(title, DOWN, buff=0.15)
        self.play(FadeIn(subtitle, shift=DOWN * 0.1), run_time=0.5)

        state = {"D": "d0", "I": "i0", "G": "n1", "S": "s1", "L": "c0"}
        network = self.draw_network(state)
        self.play(FadeIn(network), run_time=0.8)
        self.highlight_evidence_nodes()

        counters = self.create_weight_panel()
        self.play(FadeIn(counters), run_time=0.5)

        calc_line = Text("Calculando pesos de evidencia...", font_size=22, color=BLUE_C)
        calc_line.to_edge(DOWN, buff=0.28)
        self.play(FadeIn(calc_line), run_time=0.4)

        n_samples = 18
        weight_total = 0.0
        weight_hits = 0.0

        for k in range(1, n_samples + 1):
            sample, w, hit_w = self.lw_sample_once()
            self.animate_state_update(sample)
            self.highlight_weighted_sample()

            i_val = sample["I"]
            g_val = sample["G"]
            s_idx = self.states["S"].index("s1")
            l_idx = self.states["L"].index("c0")
            w_s = self.p_s[i_val][s_idx]
            w_l = self.p_l[g_val][l_idx]

            weight_total += w
            weight_hits += hit_w
            est = weight_hits / weight_total if weight_total > 0 else 0.0

            steps = [
                f"Muestra {k}: {self.node_label('I')}={self.fmt_state(i_val)}, "
                f"{self.node_label('G')}={self.fmt_state(g_val)}",
                f"P({self.node_label('S')}={self.fmt_state('s1')}|"
                f"{self.node_label('I')}={self.fmt_state(i_val)}) = {w_s:.3f}",
                f"P({self.node_label('L')}={self.fmt_state('c0')}|"
                f"{self.node_label('G')}={self.fmt_state(g_val)}) = {w_l:.3f}",
                f"w = {w_s:.3f} * {w_l:.3f} = {w:.4f}",
            ]
            calc_line = self.show_lw_calc_steps(calc_line, steps)

            self.update_weight_panel(k, weight_total, weight_hits, est, sample["I"] == "i1")
            self.wait(0.35)

        final_text = Text(
            f"Estimacion final ponderada: {weight_hits:.3f}/{weight_total:.3f} = {weight_hits / max(weight_total,1e-9):.3f}",
            font_size=26,
            color=YELLOW,
        )
        final_text.to_edge(DOWN, buff=0.25)
        self.play(ReplacementTransform(calc_line, final_text), run_time=0.5)
        self.wait(1.2)

    def make_lw_calc_block(self, steps):
        lines = [Text(line, font_size=22, color=WHITE) for line in steps]
        block = VGroup(*lines)
        block.arrange(DOWN, aligned_edge=LEFT, buff=0.08)
        block.to_edge(DOWN, buff=0.28)
        if block.width > 12.5:
            block.scale_to_fit_width(12.5)
        return block

    def show_lw_calc_steps(self, previous_line, steps):
        block = self.make_lw_calc_block(steps)
        if previous_line is not None:
            self.play(FadeOut(previous_line), run_time=0.2)

        self.play(FadeIn(block[0]), run_time=0.3)
        self.wait(0.2)
        self.play(FadeIn(block[1]), run_time=0.3)
        self.wait(0.2)
        self.play(FadeIn(block[2]), run_time=0.3)
        self.wait(0.2)
        self.play(FadeIn(block[3]), run_time=0.3)
        self.wait(0.6)
        return block

    def create_weight_panel(self):
        self.count_text = Text("Muestras: 0", font_size=22)
        self.weight_text = Text("Peso total: 0.000", font_size=22, color=BLUE_C)
        self.hit_weight_text = Text(
            f"Peso hits {self.node_label('I')}={self.fmt_state('i1')}: 0.000",
            font_size=22,
        )
        self.est_text = Text("Estimacion: 0.000", font_size=22, color=YELLOW)
        self.last_hit_text = Text("Ultima muestra: --", font_size=22, color=GRAY_A)

        panel = VGroup(
            self.count_text,
            self.weight_text,
            self.hit_weight_text,
            self.est_text,
            self.last_hit_text,
        )
        panel.arrange(DOWN, aligned_edge=LEFT, buff=0.08)
        panel.to_corner(UR, buff=0.45).shift(DOWN * 1.6)
        return panel

    def update_weight_panel(self, n, weight_total, weight_hits, est, is_hit):
        new_count = Text(f"Muestras: {n}", font_size=22).move_to(self.count_text)
        new_weight = Text(f"Peso total: {weight_total:.3f}", font_size=22, color=BLUE_C).move_to(self.weight_text)
        new_hit_weight = Text(
            f"Peso hits {self.node_label('I')}={self.fmt_state('i1')}: {weight_hits:.3f}",
            font_size=22,
        ).move_to(self.hit_weight_text)
        new_est = Text(f"Estimacion: {est:.3f}", font_size=22, color=YELLOW).move_to(self.est_text)
        last = "si aporta hit" if is_hit else "no aporta hit"
        new_last = Text(f"Ultima muestra: {last}", font_size=22, color=GREEN_C if is_hit else GRAY_A)
        new_last.move_to(self.last_hit_text)

        self.play(
            ReplacementTransform(self.count_text, new_count),
            ReplacementTransform(self.weight_text, new_weight),
            ReplacementTransform(self.hit_weight_text, new_hit_weight),
            ReplacementTransform(self.est_text, new_est),
            ReplacementTransform(self.last_hit_text, new_last),
            run_time=0.22,
        )
        self.count_text = new_count
        self.weight_text = new_weight
        self.hit_weight_text = new_hit_weight
        self.est_text = new_est
        self.last_hit_text = new_last

    def highlight_weighted_sample(self):
        self.play(
            self.node_circles["S"].animate.set_stroke(YELLOW, width=4.5),
            self.node_circles["L"].animate.set_stroke(YELLOW, width=4.5),
            run_time=0.2,
        )
        self.play(
            self.node_circles["S"].animate.set_stroke(BLUE, width=4),
            self.node_circles["L"].animate.set_stroke(BLUE, width=4),
            run_time=0.18,
        )

    def lw_sample_once(self):
        # Sample non-evidence variables and clamp evidence values.
        d = self.sample_cat(["d0", "d1"], [self.p_d["d0"], self.p_d["d1"]])
        i = self.sample_cat(["i0", "i1"], [self.p_i["i0"], self.p_i["i1"]])
        g = self.sample_cat(["n1", "n2", "n3"], self.p_g[(i, d)])
        s = "s1"
        l = "c0"

        w_s = self.p_s[i][1]  # P(S=s1 | I=i)
        w_l = self.p_l[g][0]  # P(L=c0 | G=g)
        w = w_s * w_l
        hit_w = w if i == "i1" else 0.0
        return {"D": d, "I": i, "G": g, "S": s, "L": l}, w, hit_w
