# Kairos Control

Kairos Control is a graphical user interface in Python/PySide6 for a DIY CNC mill. 
It uses the LinuxCNC Python API and EtherCAT components. 
The goal is an intuitive design and workflow.

## Features (planned)
- Manual and automatic machine control (jogging, MDI, program execution)
- In-app tool and file management
- Workpiece-based file management: multiple G-code programs per part, sorted and versioned together
- Basic material removal simulation (optional, isolated module)
- Built for a vertical (portrait) touch screen

Status: Phase 1

## Roadmap:
1. Backend logic (domain, backend interface, controler)
2. Main page
3. Manual and automatic controll (Jogging, MDI, etc.)
5. Tool library
6. Workpiece library
7. Material removal simulation
8. Analytics (scope to be defined)

## Used components
- Leadshine EL7 EC servodrives
- Beckhoff EK1100 IO (EL2008, EL1008)
- OMRON 3G3M1-A4030-ECT VFD
- LattePanda Mu

---
PS: I am neither a programmer nor an electrical engineer. I study mechanical engineering
and build this alongside my studies.

AI usage: concepts, designs, icons, etc. are done by me. I use AI as a guide for programming,
for repetitive tasks and for debugging. Parts written completely by AI are marked as such
(primarily tests, the simulated backend and the material removal simulation; OpenGL is witchcraft).
