#!/usr/bin/env python3

from ftdi_client import D2XXTest
import pygame_widgets
import pygame
from pygame_widgets.slider import Slider
from pygame_widgets.textbox import TextBox
from pygame_widgets.button import Button
from pygame_widgets.toggle import Toggle


BACKGROUND_COLOUR = (255, 255, 255)
CURRENT_PATCH = 63

FTDI_CLIENT = D2XXTest()
                

def patchButtonsClick(direction):
    global CURRENT_PATCH
    CURRENT_PATCH += direction
    panel.contents["Patches"].contents["PatchNo"].setText(str(CURRENT_PATCH))
    FTDI_CLIENT.loadPatch(CURRENT_PATCH)
    panel.process_patch_data(FTDI_CLIENT.getAllParameters())

class Group:
    def __init__(self, name, x, y, width, height, **kwargs):
        self.name = name
        self.x = x
        self.y = y
        self.rect1 = pygame.Rect(x, y, width, height)
        self.rect2 = pygame.Rect(x+2, y+2, width-4, height-4)
        self.contents = {}

    def add(self, widget, name=None):
        if name is None:
            self.contents[widget.name] = widget
        else:
            self.contents[name] = widget

    def draw(self, win):
        win.fill((0,0,0), self.rect1)
        win.fill((BACKGROUND_COLOUR), self.rect2)
        for widget in self.contents:
            if isinstance(self.contents[widget], Group):
                self.contents[widget].draw(win)

    def update(self):
        for widget in self.contents:
            if not type(self.contents[widget]) in [Button, TextBox, Toggle]:
                self.contents[widget].update()

    def process_patch_data(self, data):
        for widget in self.contents:
            if isinstance(self.contents[widget], Group):
                self.contents[widget].process_patch_data(data)
            elif isinstance(self.contents[widget], VerticalSlider):
                self.contents[widget].past_value = data[self.contents[widget].control_number]
                self.contents[widget].slider.setValue(data[self.contents[widget].control_number])
                self.contents[widget].textbox.setText(data[self.contents[widget].control_number])
            elif isinstance(self.contents[widget], XVToggle):
                self.contents[widget].process_patch_data(data)
                #self.contents[widget].slider.setValue(data[self.contents[widget].control_number])
                #self.contents[widget].textbox.setText(data[self.contents[widget].control_number])


class SliderBank:
    def __init__(self, win, x, y, width, height, num_sliders, control_numbers=[], **kwargs):
        if len(control_numbers) != num_sliders:
            raise ValueError("Number of control numbers must match number of sliders")
        self.sliders = []
        for i in range(num_sliders):
            self.sliders.append(VerticalSlider(win, x + i * (width * 2), y, width, height, control_numbers[i], **kwargs))

    def update(self):
        for slider in self.sliders:
            slider.update()

class VerticalSlider:
    def __init__(self, win, x, y, width, height, control_number, **kwargs):
        self.slider = Slider(win, x, y, width, height, vertical=True, **kwargs)
        self.textbox = TextBox(win, x-5, y + height + 30, width+5, width+5, 
                               fontSize=20, 
                               borderColour=(BACKGROUND_COLOUR), 
                               colour=(BACKGROUND_COLOUR), 
                               textColour=(0, 0, 0))
        self.textbox.disable()
        self.control_number = control_number
        self.past_value = 0
        if "name" in kwargs:
            self.name = kwargs["name"]
        else:
            self.name = str(control_number)

    def update(self):
        updated_value = self.slider.getValue()
        if updated_value != self.past_value:
            self.textbox.setText(updated_value)
            FTDI_CLIENT.writeParameter(self.control_number, updated_value)
            self.past_value = updated_value

class XVToggle:
    def __init__(self, win, x, y, width, height, control_number, **kwargs):
        self.toggle = Toggle(win, x, y, width, height, **kwargs)
        self.name = kwargs["name"]
        self.control_number = control_number
        self.past_value = 0

    def update(self):
        new_value = self.toggle.getValue()
        if new_value != self.past_value:
            print("writing toggle value %d %d" % (self.control_number, new_value))
            FTDI_CLIENT.writeParameter(self.control_number, new_value)
            self.past_value = new_value

    def process_patch_data(self, data):
        if data[self.control_number] != self.past_value:
                #print("setting toggle value %d %d" % (self.control_number, data[self.control_number]))
                if data[self.control_number] > 0:
                    self.past_value = 1
                else:
                    self.past_value = 0
                self.toggle.toggle()

pygame.init()
win = pygame.display.set_mode((1024,768))

panel = Group("main", 0, 0, 1024, 768)

panel.add(Group("Oscillator1", 0, 0, 450, 250))

panel.add(Group("Patches", 450, 0, 450, 250))
panel.contents["Patches"].add(Button(win, 500, 50, 100, 50, text="Up", onClick=patchButtonsClick, onClickParams=[1]), name="PatchUp")
panel.contents["Patches"].add(Button(win, 650, 50, 100, 50, text="Down", onClick=patchButtonsClick, onClickParams=[-1]), name="PatchDown")
panel.contents["Patches"].add(TextBox(win, 500, 100, 50, 50, fontSize=20, borderColour=(BACKGROUND_COLOUR), colour=(BACKGROUND_COLOUR), textColour=(0, 0, 0)), name="PatchNo")

#bank = SliderBank(win, 100, 100, 25, 200, 5, [], max=127, step=1, initial=0)

panel.contents["Oscillator1"].add(XVToggle(win, 25, 25, 40, 20, 1, name="Osc1OnOff"))
panel.contents["Oscillator1"].add(XVToggle(win, 25, 75, 40, 20, 2, name="Osc2OnOff"))
panel.contents["Oscillator1"].add(XVToggle(win, 25, 125, 40, 20, 3, name="Osc3OnOff"))
panel.contents["Oscillator1"].add(XVToggle(win, 25, 175, 40, 20, 4, name="Osc4OnOff"))

panel.contents["Oscillator1"].add(VerticalSlider(win, 150, 25, 20, 160, 27, max=255, step=1, initial=0))
panel.contents["Oscillator1"].add(VerticalSlider(win, 200, 25, 20, 160, 28, max=255, step=1, initial=0))
panel.contents["Oscillator1"].add(VerticalSlider(win, 250, 25, 20, 160, 29, max=255, step=1, initial=0))
panel.contents["Oscillator1"].add(VerticalSlider(win, 300, 25, 20, 160, 30, max=255, step=1, initial=0))

FTDI_CLIENT.openDev()

run = True
while run:
    events = pygame.event.get()
    for event in events:
        if event.type == pygame.QUIT:
            pygame.quit()
            run = False
            FTDI_CLIENT.closeDev()
            quit()

    win.fill(BACKGROUND_COLOUR)
    panel.draw(win)

    # this walks through the panel and updates all the widgets
    panel.update()

    pygame_widgets.update(events)
    pygame.display.update()