import hashlib


def solve_apple_challenge(stamp: str) -> str:
    leading_zeros = int(stamp.split(":")[1])
    circle_num = 0

    while True:
        circle_challenge = stamp + '::' + str(circle_num)
        hashvalue = hashlib.sha1(circle_challenge.encode()).digest()
        big_int = int.from_bytes(hashvalue, 'big')
        zeroes = 160 - big_int.bit_length()
        if zeroes >= leading_zeros:
            return circle_challenge
        circle_num += 1
