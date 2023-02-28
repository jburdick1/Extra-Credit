import turtle
import random

def drunkard_walk(X_0,Y_0, steps):
    turtle.penup()
    turtle.goto(X_0,Y_0)
    turtle.pendown()
    turtle.pencolor('black')
    turtle.pensize(2)

    for i in range(steps):
        johns_direction = random.choice(["North","South","East","West"])
        if johns_direction == "North":
            turtle.setheading(90)
            turtle.forward(10)
        if johns_direction == "South":
            turtle.setheading(270)
            turtle.forward(10)
        if johns_direction == "East":
            turtle.setheading(0)
            turtle.forward(10)
        if johns_direction == "West":
            turtle.setheading(180)
            turtle.forward(10)

    distance = turtle.distance(X_0,Y_0)
    return distance

def main():
    X_0 = 0
    Y_0 = 0
    steps = 10
    print(f"The drunkard started from ({X_0},{Y_0}) ")
    turtle.penup()
    turtle.goto(X_0,Y_0)
    turtle.dot(10,"red")
    distance = drunkard_walk(X_0,Y_0,steps)
    print(f"After {steps} intersections, hes {distance} blocks from where he started.")
    turtle.pendown()
    turtle.goto(X_0+distance, Y_0)
    turtle.dot(10, "red")
    turtle.done()

if __name__== "__main__":
    main()

