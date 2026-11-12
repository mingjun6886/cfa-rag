# Time Value of Money: A Short Primer

Sample corpus for cfa-rag. Written for this repository and released under the MIT licence. It is not CFA Institute or Schweser material.

## Why money has a time value

A dollar received today is worth more than a dollar received in a year. Today's dollar can be invested and earn a return before the later one arrives, inflation may erode what the later dollar buys, and a promised future payment carries some risk that it will not be paid in full.

An interest rate expresses this trade-off. The same number can be read three ways: as the return an investor requires for waiting, as the discount rate that converts a future amount into its value today, or as the opportunity cost of spending money now instead of investing it.

A nominal interest rate can be thought of as a real risk-free rate plus a premium for expected inflation, plus premiums for the risks of the particular investment: default risk, liquidity risk and, for longer maturities, maturity risk.

## Future value of a single sum

Money invested today grows by the interest it earns, and in later periods it also earns interest on earlier interest. This is compounding. With an interest rate r per period and N periods, the future value of a present amount PV is:

    FV = PV × (1 + r)^N

Example: 1,000 invested for 3 years at 5% a year grows to 1,000 × 1.05^3 = 1,157.63.

When interest is compounded m times a year on a stated annual rate r, the rate per period is r/m and the number of periods is m × N:

    FV = PV × (1 + r/m)^(m × N)

Example: the same 1,000 at 5% compounded monthly for 3 years grows to 1,000 × (1 + 0.05/12)^36 = 1,161.47. More frequent compounding gives a slightly larger amount.

In the limit of continuous compounding the formula becomes:

    FV = PV × e^(r × N)

Example: 1,000 × e^(0.05 × 3) = 1,161.83.

The table below gives the future value of 1 for a few rates and horizons.

| Periods | 2% | 5% | 8% | 10% |
| 1 | 1.0200 | 1.0500 | 1.0800 | 1.1000 |
| 5 | 1.1041 | 1.2763 | 1.4693 | 1.6105 |
| 10 | 1.2190 | 1.6289 | 2.1589 | 2.5937 |

## Effective annual rate

A stated annual rate does not show the effect of compounding within the year. The effective annual rate (EAR) does:

    EAR = (1 + periodic rate)^m - 1

Example: a stated rate of 12% compounded quarterly has a periodic rate of 3%, so EAR = 1.03^4 - 1 = 12.55%. Compounded monthly, the periodic rate is 1% and EAR = 1.01^12 - 1 = 12.68%. Comparing loans or deposits by their effective rates puts them on the same footing.

## Present value of a single sum

Discounting reverses compounding. The present value of an amount FV received after N periods is:

    PV = FV / (1 + r)^N

Example: 5,000 to be received in 4 years, discounted at 6% a year, is worth 5,000 / 1.06^4 = 3,960.47 today. A higher discount rate or a longer wait lowers the present value.

## Annuities

An annuity is a series of equal payments made at equal intervals. In an ordinary annuity the payments fall at the end of each period; in an annuity due they fall at the start.

For an ordinary annuity of N payments of PMT at a rate r per period:

    PV = PMT × [1 - (1 + r)^(-N)] / r
    FV = PMT × [(1 + r)^N - 1] / r

Example: five annual payments of 200 at 4% have a present value of 200 × (1 - 1.04^(-5)) / 0.04 = 890.36 and a future value, at the date of the last payment, of 200 × (1.04^5 - 1) / 0.04 = 1,083.26.

Each payment of an annuity due arrives one period earlier, so its present value is the ordinary annuity's present value multiplied by (1 + r). For the example above, 890.36 × 1.04 = 925.98.

The same formula can be solved for the payment. A loan of 10,000 repaid in five equal year-end payments at 7% requires:

    PMT = PV × r / [1 - (1 + r)^(-N)]

which gives 10,000 × 0.07 / (1 - 1.07^(-5)) = 2,438.91 a year. Each payment covers that year's interest, and the rest repays part of the principal.

## Perpetuities

A perpetuity is an annuity that never ends. Its present value is finite because payments far in the future are worth very little today:

    PV = PMT / r

Example: a preferred share paying 4 a year forever, valued at a required return of 8%, is worth 4 / 0.08 = 50.

If the payments grow at a constant rate g that is lower than r, and the first payment PMT1 arrives one period from now:

    PV = PMT1 / (r - g)

Example: a payment of 2 next year that grows by 3% a year, discounted at 9%, is worth 2 / (0.09 - 0.03) = 33.33.

## Uneven cash flows and net present value

When cash flows differ from period to period, each one is discounted separately and the results are added. Net present value (NPV) adds the present values of all cash flows, including the initial outlay as a negative amount.

Example: a project costs 1,000 today and returns 400 at the end of each of the next three years. At a discount rate of 10%, the inflows are worth 400 / 1.1 + 400 / 1.1^2 + 400 / 1.1^3 = 994.74, so NPV = 994.74 - 1,000 = -5.26. The project falls just short of earning 10%.

The internal rate of return (IRR) is the discount rate at which NPV equals zero. For this project it is about 9.70%, slightly below the 10% required, which agrees with the negative NPV.

## Common mistakes

Match the rate to the period: a monthly cash flow needs a monthly rate. Check when the first cash flow arrives, because an annuity due and an ordinary annuity differ by one period of interest. On a financial calculator, money paid out and money received carry opposite signs; entering both with the same sign produces an error or a meaningless answer.
