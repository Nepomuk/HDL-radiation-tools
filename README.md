Hamming Tools
=============

This is my collection of tools I have written, to make my life with the Hamming code easier. If you don't know what a Hamming code is, go to see for instance the [Wikipedia](http://en.wikipedia.org/wiki/Hamming_code) page.

Hamming Table
-------------

I needed a tool that generates a lookup table for signal words and corresponding Hamming encoded words. So I wrote one.

#### Installation
You have two options:
<<<<<<< HEAD

* Clone the entire git repository.

        git clone https://github.com/Nepomuk/hamming-code.git

* [Download](https://raw.github.com/Nepomuk/hamming-code/master/hamming_table.py) the script alone and save it to some folder on your PC.

        wget https://raw.github.com/Nepomuk/hamming-code/master/hamming_table.py
=======
* Clone the entire git repository.
* Download the script alone and save it to some folder on your PC.
>>>>>>> ee60b40bc0908e6df85fd943040c39c4e33d783c

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

