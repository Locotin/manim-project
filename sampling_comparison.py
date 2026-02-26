from manim import *

class ComparacionMuestreo(Scene):
    SUBSCRIPT_MAP = str.maketrans("0123456789", "₀₁₂₃₄₅₆₇₈₉")
    NODE_LABELS = {
        "D": "Dificultad",
        "I": "Inteligencia",
        "G": "Nota",
        "S": "Saber",
        "L": "Carta",
    }

    def construct(self):
        self.setup_model()
        self.rng = __import__("random").Random(7)

        query_text = Text(
            f"Consulta: P({self.node_label('I')}={self.fmt_state('i1')} | "
            f"{self.node_label('S')}={self.fmt_state('s1')}, "
            f"{self.node_label('L')}={self.fmt_state('l0')})",
            font_size=26,
        )
        query_text.to_edge(UP)
        self.play(Write(query_text), run_time=0.9)

        expl = Text(
            "Rejection rechaza muestras sin evidencia; Likelihood Weighting usa pesos.",
            font_size=22,
            color=GRAY_A,
        )
        expl.next_to(query_text, DOWN, buff=0.15)
        self.play(FadeIn(expl, shift=DOWN * 0.1), run_time=0.6)

        axes = Axes(
            x_range=[0, 300, 50],
            y_range=[0, 1.0, 0.2],
            x_length=9.2,
            y_length=4.2,
            tips=False,
            axis_config={"include_numbers": False, "include_ticks": True, "font_size": 20},
        )
        axes.to_edge(LEFT, buff=0.6).shift(DOWN * 0.8)
        x_label = Text("muestras", font_size=20).next_to(axes.x_axis, DOWN, buff=0.1)
        y_label = Text("estimacion", font_size=20)
        y_label.rotate(PI / 2)
        y_label.next_to(axes.y_axis, LEFT, buff=0.28)
        self.play(Create(axes), FadeIn(x_label), FadeIn(y_label), run_time=0.9)

        rej_legend = VGroup(
            Dot(color=RED_C, radius=0.06),
            Text("Rejection Sampling", font_size=20, color=RED_C),
        ).arrange(RIGHT, buff=0.12)
        lw_legend = VGroup(
            Dot(color=BLUE_C, radius=0.06),
            Text("Likelihood Weighting", font_size=20, color=BLUE_C),
        ).arrange(RIGHT, buff=0.12)
        legend = VGroup(rej_legend, lw_legend).arrange(DOWN, aligned_edge=LEFT, buff=0.1)
        legend.to_corner(UR, buff=0.5).shift(DOWN * 1.1)
        self.play(FadeIn(legend), run_time=0.5)

        truth_line = axes.plot(lambda _: 0.578, x_range=[0, 300], color=GRAY_C, use_smoothing=False)
        truth_label = Text("referencia aproximada", font_size=18, color=GRAY_C)
        truth_label.next_to(axes.c2p(235, 0.578), UP, buff=0.08)
        self.play(Create(truth_line), FadeIn(truth_label), run_time=0.5)

        # Right metrics panel
        rej_title = Text("Rejection", font_size=22, color=RED_C)
        self.rej_count_text = Text("aceptadas: 0", font_size=20)
        self.rej_drop_text = Text("rechazadas: 0", font_size=20)
        self.rej_rate_text = Text("tasa rechazo: 0.0%", font_size=20)
        rej_panel = VGroup(rej_title, self.rej_count_text, self.rej_drop_text, self.rej_rate_text)
        rej_panel.arrange(DOWN, aligned_edge=LEFT, buff=0.06)
        rej_panel.next_to(legend, DOWN, aligned_edge=LEFT, buff=0.3)

        lw_title = Text("Likelihood Weighting", font_size=22, color=BLUE_C)
        self.lw_weight_text = Text("peso acumulado: 0.000", font_size=20)
        self.lw_eff_text = Text("muestras usadas: 0", font_size=20)
        lw_panel = VGroup(lw_title, self.lw_weight_text, self.lw_eff_text)
        lw_panel.arrange(DOWN, aligned_edge=LEFT, buff=0.06)
        lw_panel.next_to(rej_panel, DOWN, aligned_edge=LEFT, buff=0.25)
        self.play(FadeIn(rej_panel), FadeIn(lw_panel), run_time=0.6)

        # Running estimates
        rej_line_group = VGroup()
        lw_line_group = VGroup()
        prev_rej_point = None
        prev_lw_point = None
        prev_n = 0

        rej_accepted = 0
        rej_rejected = 0
        rej_query_hits = 0

        lw_weight_total = 0.0
        lw_weight_hits = 0.0

        total_samples = 300
        batch = 10
        for n in range(batch, total_samples + 1, batch):
            for _ in range(batch):
                accepted, is_hit = self.rejection_sample_once()
                if accepted:
                    rej_accepted += 1
                    if is_hit:
                        rej_query_hits += 1
                else:
                    rej_rejected += 1

                w, hit_w = self.lw_sample_once()
                lw_weight_total += w
                lw_weight_hits += hit_w

            rej_est = rej_query_hits / rej_accepted if rej_accepted > 0 else 0.0
            lw_est = lw_weight_hits / lw_weight_total if lw_weight_total > 0 else 0.0

            rej_point = Dot(axes.c2p(n, rej_est), color=RED_C, radius=0.035)
            lw_point = Dot(axes.c2p(n, lw_est), color=BLUE_C, radius=0.035)

            anims = [FadeIn(rej_point, scale=0.8), FadeIn(lw_point, scale=0.8)]
            if prev_rej_point is not None:
                rej_seg = Line(prev_rej_point.get_center(), rej_point.get_center(), color=RED_C, stroke_width=2.2)
                lw_seg = Line(prev_lw_point.get_center(), lw_point.get_center(), color=BLUE_C, stroke_width=2.2)
                rej_line_group.add(rej_seg)
                lw_line_group.add(lw_seg)
                anims.extend([Create(rej_seg), Create(lw_seg)])

            self.play(*anims, run_time=0.2)
            prev_rej_point = rej_point
            prev_lw_point = lw_point
            prev_n = n

            self.update_metric_texts(
                rej_accepted, rej_rejected, lw_weight_total, n
            )
            self.wait(1 / config.frame_rate)

        final_msg = Text(
            f"Conclusión: Rejection desperdicia muestras cuando la evidencia es rara; "
            f"Likelihood Weighting converge más estable.",
            font_size=20,
        )
        final_msg.scale_to_fit_width(6.2)
        final_msg.to_corner(DR, buff=0.35)
        self.play(FadeIn(final_msg, shift=UP * 0.1), run_time=0.7)
        self.wait(1.2)

    def setup_model(self):
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

    def sample_categorical(self, labels, probs):
        u = self.rng.random()
        acc = 0.0
        for label, p in zip(labels, probs):
            acc += p
            if u <= acc:
                return label
        return labels[-1]

    def ancestral_sample(self):
        d = self.sample_categorical(["d0", "d1"], [self.p_d["d0"], self.p_d["d1"]])
        i = self.sample_categorical(["i0", "i1"], [self.p_i["i0"], self.p_i["i1"]])
        g = self.sample_categorical(["g1", "g2", "g3"], self.p_g[(i, d)])
        s = self.sample_categorical(["s0", "s1"], self.p_s[i])
        l = self.sample_categorical(["l0", "l1"], self.p_l[g])
        return {"D": d, "I": i, "G": g, "S": s, "L": l}

    def rejection_sample_once(self):
        sample = self.ancestral_sample()
        evidence_ok = sample["S"] == "s1" and sample["L"] == "l0"
        if not evidence_ok:
            return False, False
        return True, sample["I"] == "i1"

    def lw_sample_once(self):
        # Evidence: S=s1, L=l0 are clamped and contribute to sample weight.
        d = self.sample_categorical(["d0", "d1"], [self.p_d["d0"], self.p_d["d1"]])
        i = self.sample_categorical(["i0", "i1"], [self.p_i["i0"], self.p_i["i1"]])
        g = self.sample_categorical(["g1", "g2", "g3"], self.p_g[(i, d)])

        w_s = self.p_s[i][1]  # P(S=s1 | I=i)
        w_l = self.p_l[g][0]  # P(L=l0 | G=g)
        w = w_s * w_l

        return w, w if i == "i1" else 0.0

    def update_metric_texts(self, acc, rej, lw_weight_total, n):
        rej_rate = (rej / max(n, 1)) * 100.0
        new_rej_acc = Text(f"aceptadas: {acc}", font_size=20)
        new_rej_drop = Text(f"rechazadas: {rej}", font_size=20)
        new_rej_rate = Text(f"tasa rechazo: {rej_rate:.1f}%", font_size=20)
        new_lw_weight = Text(f"peso acumulado: {lw_weight_total:.3f}", font_size=20)
        new_lw_eff = Text(f"muestras usadas: {n}", font_size=20)

        new_rej_acc.move_to(self.rej_count_text)
        new_rej_drop.move_to(self.rej_drop_text)
        new_rej_rate.move_to(self.rej_rate_text)
        new_lw_weight.move_to(self.lw_weight_text)
        new_lw_eff.move_to(self.lw_eff_text)

        self.play(
            ReplacementTransform(self.rej_count_text, new_rej_acc),
            ReplacementTransform(self.rej_drop_text, new_rej_drop),
            ReplacementTransform(self.rej_rate_text, new_rej_rate),
            ReplacementTransform(self.lw_weight_text, new_lw_weight),
            ReplacementTransform(self.lw_eff_text, new_lw_eff),
            run_time=0.08,
        )
        self.rej_count_text = new_rej_acc
        self.rej_drop_text = new_rej_drop
        self.rej_rate_text = new_rej_rate
        self.lw_weight_text = new_lw_weight
        self.lw_eff_text = new_lw_eff

    def fmt_state(self, token):
        if len(token) >= 2 and token[0].isalpha() and token[1:].isdigit():
            return token[0] + token[1:].translate(self.SUBSCRIPT_MAP)
        return token

    def node_label(self, node):
        return self.NODE_LABELS.get(node, node)
