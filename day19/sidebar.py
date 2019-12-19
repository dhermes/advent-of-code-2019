def main():
    # col_L = A row + B
    A, B = 0.732850134024908, 0.41820609837524864
    # col_R = C row + D
    C, D = 0.9164521623007768, -0.42883374137547786
    # width = col_R - col_L + 1 = (C - A) row + (D - B + 1)
    coeff = C - A
    constant = D - B + 1
    # Solve width == 100
    row_100 = (100 - constant) / coeff
    print(f"row_100: {row_100}")

    row_100 = int(row_100)
    print(f"row_100: {row_100}")
    left_col100 = A * row_100 + B
    print(f"left_col100: {left_col100}")
    right_col100 = C * row_100 + D
    print(f"right_col100: {right_col100}")


if __name__ == "__main__":
    main()
