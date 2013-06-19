HDL Radiation Protection Tools
==============================

This is my collection of tools I have written, to make my life with radiation protection for HDL code and in particular the Hamming code easier. If you don't know what a Hamming code is, go to see for instance the [Wikipedia](http://en.wikipedia.org/wiki/Hamming_code) page.

Contents:

* [Hamming Table](#hamming-table)
* [VHDL Halo Constants](#vhdl-halo-constants)
* [Flip Flop Finder](#flip-flop-finder)

* auto-gen TOC:
{:toc}

Hamming Table
-------------

I needed a tool that generates a lookup table for signal words and corresponding Hamming encoded words. So I wrote one.

Files belonging to this part:

* `hamming_table.py`


### Installation
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


### Usage

```bash
./hamming_table.py [<singal_length>]
```

**Parameter:**

* `singal_length`, _optional_:  Length of the signal word. Default = 4.

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

Files belonging to this part:

* `hamming_table.py`


### Installation

Same as above, except that you have to make another script executable:

```bash
chmod u+x vhdl_halo_constat.py
```

### Usage

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

Btw: `state_type` in this example would be a subtype of a `std_logic_vector`:

```
subtype state_type is std_logic_vector(4 downto 0);
```


Flip Flop Finder
----------------

I wanted to create a testbench that simulates SEU in all used flip flops. This script searches in a verilog file, which is the output of a synthesis process, for standard cells representing flip flops and writes a list with the paths to these flip flops. In the final file there is also a procedure to generate a SEU in a selected flip flop, using the tools from Cadence.
If you are using another system to develop, you have to search for alternatives. But this script might give you a starting point for your work.

It is based on this [verlog parser](https://github.com/yellekelyk/PyVerilog) by [yellekelyk](https://github.com/yellekelyk) which uses the [pyparsing](http://pyparsing.wikispaces.com/) module.

The files belonging to this part a located in the subfolder `flipflopfinder`.


### Installation

Basically the same as above, so you have to make another script executable:

```bash
chmod u+x flipflopfinder.py
```

#### Python modules
Furthermore you might have to install some dependencies for this script. It uses several python modules, which don't come with the default installation. I recommend installing these with [easy\_install](http://pythonhosted.org/distribute/easy_install.html), because it is just very easy.
If you don't have super user access (like in my case) you may also go with a virtual python library. The way, how to do that, is described in the [easy\_install documentation](http://pythonhosted.org/distribute/easy_install.html#custom-installation-locations).

Required python modules:

```
Cheetah
PyYAML
ordereddict
pyparsing
wsgiref
```

Note: If you are using python 2.x, you have to stick to the last pyparsing version prior 2.x, which would mean `easy_install pyparsing==1.5.6`.


#### Modify standard cells
This step is optional, but I recommend you to do it. What we will do is basically to add something to the standard cell that enables the testbench to flip the output value of a flip flop. The alternative is to change the input value of the flip flop at a rising edge of the clock, therefore overwriting the flip flops supposed value. But the input line might also be connected to another flip flop or _whatever_ logic, so for some cases you end up changing more than one flip flop at a time.

First you have to locate your standard cell directory and make a local copy of it. A starting point for searching could be the `cds.lib` file for NCLaunch. In there were these lines at my setup:

```
DEFINE cmos8rf_lib /usr/ibm_lib/cmos8_relDM/ibm_cmos8rf/std_cell/relDM/verilog/cmos8rf_lib
DEFINE worklib ./worklib
```

The directory you need to copy is then `/usr/ibm_lib/cmos8_relDM/ibm_cmos8rf/std_cell/relDM/verilog/`. After done this, locate your flip flop modules. I went with the basic modules and not with the primitives, because the latter produced some strange effects. For me I had to change the following modules:

```
DFF.v, DFFR.v, DFFS.v, DFFSR.v, SDFF.v, SDFFR.v, SDFFS.v, SDFFSR.v
```

I put my [DFFR.v](https://github.com/Nepomuk/HDL-radiation-tools/blob/master/flipflopfinder/DFFR.v) as an example in this repository and commented, what you have to change. The relevant part is this:

```verilog
reg SEU = 1'b0;
always @(posedge CLK) begin
  SEU <= 1'b0;
end

wire qout, qout2;
assign qout2 = (SEU) ? ~qout : qout;

DFF_ASYNR  r1 (qout,CLK,D,RN,notifier);
buf        b0 (Q, qout2);
not        i1 (QBAR, qout2);
```

To give some explaination for the changes: The `SEU` signal is initialized with low value and can only be changed to high by a function like `nc_force` from your testbench. It gets reset to low with the next clock cycle, because we want to accept a new value with the next rising edge.
If `SEU` is high, it negates the `qout` signal (which is the output of the flip flop look-up table `DFF_ASYNR`) and transfers it via `qout2` to the output lines.

After you have made all modifications, you need to tell your simulator where to find the modified standard cell library. For me the cds.lib looks now like this:

```
#DEFINE cmos8rf_lib /usr/ibm_lib/cmos8_relDM/ibm_cmos8rf/std_cell/relDM/verilog/cmos8rf_lib
DEFINE cmos8rf_lib ./std_cell_SEU/verilog/cmos8rf_lib
DEFINE worklib ./worklib
```


### Usage

```bash
./flipflopfinder.py <input file> <output file> <top level instance name>
```

**Parameter:**

* `input file`: The path to the input verilog file, which comes out of your synthesis.
* `output file`: The path to the VHDL file, which will include the list of flip flops and the precedure to use it into your testbench.
* `top level instance name`: To get the path to the flip flops correct, we also need to include the name of your top level instance. Since this is defined in the testbench, the script has no way of knowing about that, therefore you have to give it as a parameter.

**Output**

Depending on the verbose setting in the script (see the first lines of code) you will get some status information. And of course the output file

#### Include into testbench

You have to make three steps. Variables starting with $ are replaced in the final output file depending on your inputs. See the comments in top of the output file for copy-paste-ready examples.

1. Include the package in the header.

        use work.${packageName}.all;

2. _Optional step_: Link the mirror signals to the acutal flip flop values. If you are sticking to unchanged standard cells, this is needed to determine, which value is the current one and which is the "switched value".

        process begin
          for i in 0 to N_FLIPFLOPS-1 loop
            nc_mirror( "${packageName}.flipflop_mirror[" & integer'image(i) & "]", getFlipFlop(i) );
          end loop;
        end process;

3. Create a single event upset by calling the procedure from the output file.

        sim_SEU_FF( FF_ID_to_test, SEU_active, clk, clk_period, method );

  The parameters are the following:

    * `FF_ID_to_test`: The integer ID of the flip flop to test
    * `SEU_active`: A flag informing the testbench when the SEU is happening
    * `clk`: The clock driving this flip flop
    * `clk_period`: Clock period of this clock.
    * `method`: Select the method generating a SEU: '0' input line, '1' flip inside (modified std. cell)
