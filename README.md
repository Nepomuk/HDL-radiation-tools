Hamming Tools
=============

This is my collection of tools I have written, to make my life with the Hamming code easier. If you don't know what a Hamming code is, go to see for instance the [Wikipedia](http://en.wikipedia.org/wiki/Hamming_code) page.

Hamming Table
-------------

I needed a tool that generates a lookup table for signal words and corresponding Hamming encoded words. So I wrote one.

#### Installation
You have two options:

* Clone the entire git repository.

        git clone https://github.com/Nepomuk/hamming-code.git

* [Download](https://raw.github.com/Nepomuk/hamming-code/master/hamming_table.py) the script alone and save it to some folder on your PC.

        wget https://raw.github.com/Nepomuk/hamming-code/master/hamming_table.py

If you want to call the script directly, you first have to make it executable:

```bash
chmod u+x hamming_table.py
./hamming_table.py
```

Otherwise you are fine with calling it using the python interpreter: `python hamming_table.py`


#### Usage

```bash
./hamming_table.py [<singal_length>]
```

**Parameter:**

* `singal_length` (*optional*): Length of the signal word. Default = 4.

**Return:**

```bash
$ ./hamming_table.py
Printing table for Ham(7,4):
0000   0000000
0001   0000111
0010   0011001
0011   0011110
0100   0101010
0101   0101101
0110   0110011
0111   0110100
1000   1001011
1001   1001100
1010   1010010
1011   1010101
1100   1100001
1101   1100110
1110   1111000
1111   1111111
```


VHDL Halo Constants
-------------------

For my development of a Hamming encoded VHDL project, I wanted to simplify the work when it came to state machines. If want to definie your own states, including valid and halo states, you end up writing a lot of zeros and ones - especially when you have lots of states. This program helps you generate the definition of these halo states (generating all the states with one bit flipped).

#### Installation

Same as above, except that you have to make another script executable:

```bash
chmod u+x vhdl_halo_constat.py
```

#### Usage

```bash
./vhdl_halo_constat.py <constant name> <valid signal>
```

**Parameter:**

* `constant name`: A valid VHDL name for a signal/constant, for instance `IDLE`.
* `valid signal`: The original signal for the state as a string of bits. So for instance `00111`.

**Output**

Running with the example values given in the parameter section, the program will print out this:

```bash
$ ./vhdl_halo_constant.py IDLE 00111
constant IDLE_0 : state_type := "00110";
constant IDLE_1 : state_type := "00101";
constant IDLE_2 : state_type := "00011";
constant IDLE_3 : state_type := "01111";
constant IDLE_4 : state_type := "10111";
```

You can copy and paste this into your VHDL project and have all the halo states of the initial IDLE state, where just one bit is flipped.

Btw: `state_type` in this example would be a subtype of a `std_logic_vector:

```
subtype state_type is std_logic_vector(4 downto 0);
```
