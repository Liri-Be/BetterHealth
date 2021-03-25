"""
this series always ends with 1, it was shown with many examples but never proofed.
"""


def series(number):
    print(number)
    if number == 1:
        return
    else:
        if number % 2 == 0:
            return series(number/2)
        else:
            return series(3*number+1)


def main():
    for i in range(1, 100000000000000000000000000000000000000000000):
        series(i)
        print("\n")


if __name__ == '__main__':
    main()
