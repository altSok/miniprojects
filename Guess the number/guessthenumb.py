import random
from unittest import enterModuleContext


def guess():
    number = random.randint(1,10)
    guessed = False

    while not guessed:
        try:
            i = int(input("Enter a number: "))
        except ValueError:
            print("Please enter a number")
            continue

        if i < number:
            print("Your guess is incorrect, try higher")

        elif i > number:
            print("Your guess is incorrect, try lower")

        else:
            print(f"You guessed correctly, congratulations!")
            guessed = True

            again = input("Wanna try again?(+, -) : ")
            if again == "+":
                guess()
            else:
                print("Have a good time!")
                input("Press enter to quit...")



guess()

