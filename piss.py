from sense_hat import SenseHat
import random
import time

class Piss:
    def __init__(self):
        self.sense = SenseHat() 
        self.coordinates = [random.randint(0,100), random.randint(0,100)]
        self.is_locked = True  # Default state
        self.sensitivity = 1  # Movement per joystick press
        
        self.sense.stick.direction_any = self.joystick_moved
        

    
    def sense_light(self):
        red = (255,0,0)
        yellow = (255, 255, 0)
        blinking_red = (255,0,0)
        green = (0,255,0)


        if self.is_locked:
            self.sense.clear((red))
        else:
           self.sense.clear((green))

    def joystick_moved(self, event):
        if event.action != "pressed":
            return
        
        x, y = self.coordinates

        if event.direction == "up":
            y += self.sensitivity
        elif event.direction == "down":
            y -= self.sensitivity
        elif event.direction == "left":
            x -= self.sensitivity
        elif event.direction == "right":
            x += self.sensitivity

        # Clamp coordinates to 0–100
        x = max(0, min(100, x))
        y = max(0, min(100, y))
        
        self.coordinates = [x,y]
        

if __name__ == "__main__":
    scooter = Piss()
    scooter.sense_light()

    try:
        while True:
          print(scooter.coordinates)
          time.sleep(1)
          scooter.sense_light()
          if scooter.is_locked:
            scooter.is_locked = False
          else:
            scooter.is_locked = True
            
    except Exception as e:
        scooter.sense.clear()
        print(e)