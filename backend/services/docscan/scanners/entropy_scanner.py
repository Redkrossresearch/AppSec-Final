import math

def calculate_entropy(data):

    if not data:

        return 0

    entropy = 0

    for x in range(256):

        p_x = data.count(
            chr(x)
        ) / len(data)

        if p_x > 0:

            entropy += - p_x * math.log2(
                p_x
            )

    return round(
        entropy,
        2
    )