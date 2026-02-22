from manim import *


class AnimacionBasica(Scene):
    def construct(self):
        titulo = Text("Arthur Bobo Triple hijueputa", font_size=72)
        circulo = Circle(color=BLUE).shift(LEFT * 2)
        cuadrado = Square(color=GREEN).shift(RIGHT * 2)

        self.play(Write(titulo))
        self.wait(0.5)
        self.play(FadeOut(titulo))

        self.play(Create(circulo), Create(cuadrado))
        self.play(circulo.animate.set_fill(BLUE, opacity=0.5))
        self.play(Rotate(cuadrado, angle=PI / 4))
        self.play(circulo.animate.shift(RIGHT * 2), cuadrado.animate.shift(LEFT * 2))
        self.wait(1)
