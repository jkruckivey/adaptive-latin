# Basic Arithmetic Formulas in Excel

## Introduction

Excel's power comes from its ability to perform calculations automatically. The three most fundamental functions you'll use are SUM, AVERAGE, and COUNT. These functions form the foundation of data analysis in spreadsheets.

## The SUM Function

The SUM function adds all numbers in a range. The syntax is:

```
=SUM(range)
```

**Example:** If cells A1 through A5 contain the values 10, 20, 30, 40, and 50, then `=SUM(A1:A5)` returns 150.

**When to use it:** Calculating totals for sales, expenses, quantities, scores, or any set of numbers that need to be added together.

## The AVERAGE Function

The AVERAGE function calculates the arithmetic mean (average) of a set of numbers. The syntax is:

```
=AVERAGE(range)
```

**Example:** For the same data (10, 20, 30, 40, 50), `=AVERAGE(A1:A5)` returns 30.

**When to use it:** Finding typical values, calculating grades, determining average performance metrics, or analyzing trends.

## The COUNT Function

The COUNT function counts how many cells in a range contain numeric values. The syntax is:

```
=COUNT(range)
```

**Example:** If A1:A10 contains 7 numbers and 3 empty cells, `=COUNT(A1:A10)` returns 7.

**When to use it:** Determining sample size, counting data points, or verifying data entry completeness.

## Practical Tips

1. **Always start with =**: Every formula in Excel must begin with an equals sign
2. **Use ranges**: Instead of `=A1+A2+A3+A4+A5`, use `=SUM(A1:A5)`
3. **Check your selection**: After typing the function, Excel highlights the selected range
4. **Multiple ranges**: You can use `=SUM(A1:A5, C1:C5)` to add multiple ranges

## Common Mistakes to Avoid

- Forgetting the equals sign (typing SUM(A1:A5) instead of =SUM(A1:A5))
- Including text cells in AVERAGE (Excel ignores them, but be aware)
- Using COUNT when you mean COUNTA (COUNT only counts numbers, COUNTA counts all non-empty cells)

## Practice Scenario

Imagine you're analyzing monthly sales data. You have sales figures for each day in column B (B2:B31 for a 30-day month). You would use:
- `=SUM(B2:B31)` for total monthly sales
- `=AVERAGE(B2:B31)` for average daily sales
- `=COUNT(B2:B31)` to verify all 30 days have data entered
