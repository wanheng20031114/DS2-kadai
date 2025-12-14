import flet as ft
import math


class CalcButton(ft.ElevatedButton):
    def __init__(self, text, on_click, expand=1, bgcolor=None, color=None):
        super().__init__(
            text=text,
            expand=expand,
            bgcolor=bgcolor,
            color=color,
            on_click=on_click,
            data=text,
        )


class Calculator(ft.Column):

    def __init__(self):
        super().__init__()
        self.result = ft.Text("0", size=40, color=ft.Colors.WHITE)

        self.buttons_layout = [
            ["sin", "cos", "tan", "log"],
            ["ln", "^", "AC", "/"],
            ["7", "8", "9", "*"],
            ["4", "5", "6", "-"],
            ["1", "2", "3", "+"],
            ["0", ".", "="],
        ]

        container = ft.Container(
            width=350,
            bgcolor=ft.Colors.BLACK,
            border_radius=20,
            padding=20,
            content=self.build_layout(),
        )

        self.controls = [container]

        self.current = ""
        self.last = ""
        self.op = None

    def build_layout(self):
        rows = [
            ft.Row([self.result], alignment="end")
        ]

        for row_buttons in self.buttons_layout:
            row = ft.Row([], spacing=5)
            for b in row_buttons:
                btn = self.create_button(b)
                row.controls.append(btn)
            rows.append(row)

        return ft.Column(rows, spacing=10)

    def create_button(self, text):
        # 補充：　Scientific functions
        if text in ["sin", "cos", "tan", "log", "ln", "^"]:
            return CalcButton(
                text,
                self.button_clicked,
                bgcolor=ft.Colors.BLUE_400,
                color=ft.Colors.WHITE,
    )
        # Extra action buttons
        if text in ["AC", "+/-", "%"]:
            return CalcButton(
                text,
                self.button_clicked,
                bgcolor=ft.Colors.BLUE_GREY_100,
                color=ft.Colors.BLACK,
            )
        # Operators
        if text in ["+", "-", "*", "/", "="]:
            return CalcButton(
                text,
                self.button_clicked,
                bgcolor=ft.Colors.ORANGE,
                color=ft.Colors.WHITE,
            )
        # Digits
        if text == "0":
            return CalcButton(
                text,
                self.button_clicked,
                expand=2,
                bgcolor=ft.Colors.WHITE24,
                color=ft.Colors.WHITE,
            )
        return CalcButton(
            text,
            self.button_clicked,
            bgcolor=ft.Colors.WHITE24,
            color=ft.Colors.WHITE,
        )

    def button_clicked(self, e):
        v = e.control.data

        if v in ["sin", "cos", "tan", "log", "ln"]:
            if self.current:
                try:
                    x = float(self.current)
                    if v == "sin":
                        self.current = str(math.sin(math.radians(x)))
                    elif v == "cos":
                        self.current = str(math.cos(math.radians(x)))
                    elif v == "tan":
                        self.current = str(math.tan(math.radians(x)))
                    elif v == "log":
                        if x <= 0:
                            raise ValueError
                        self.current = str(math.log10(x))
                    elif v == "ln":
                        self.current = str(math.log(x))
                except:
                    self.current = "Error"

                self.result.value = self.current
                self.result.update()
            return

        if v == "^":
            if self.current:
                self.last = self.current
                self.current = ""
                self.op = "^"
            return

        if v == "AC":
            self.current = ""
            self.last = ""
            self.op = None
            self.result.value = "0"
            self.result.update()
            return

        if v in ["+", "-", "*", "/"]:
            if self.current:
                self.last = self.current
                self.current = ""
            self.op = v
            return

        if v == "=":
            if self.op and self.last and self.current:
                try:
                    if self.op == "^":
                        self.current = str(float(self.last) ** float(self.current))
                    else:
                        self.current = str(eval(self.last + self.op + self.current))
                except:
                    self.current = "Error"

                self.result.value = self.current
                self.result.update()
            return

        # "+/-"
        if v == "+/-":
            if self.current.startswith("-"):
                self.current = self.current[1:]
            else:
                self.current = "-" + self.current
            self.result.value = self.current
            self.result.update()
            return

        # "%"
        if v == "%":
            if self.current:
                try:
                    self.current = str(float(self.current) / 100)
                except:
                    self.current = "Error"
                self.result.value = self.current
                self.result.update()
            return

        # digits / "."
        self.current += v
        self.result.value = self.current
        self.result.update()


def main(page: ft.Page):
    page.title = "Calculator"
    page.bgcolor = ft.Colors.BLACK
    page.horizontal_alignment = "center"
    page.vertical_alignment = "center"

    calc = Calculator()
    page.add(calc)


ft.app(main)
