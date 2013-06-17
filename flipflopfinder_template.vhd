-- # Automatically generated VHDL file to import into testbench.
-- #     generated on $datetime
--
-- # To use this package, simply import it into your testbench:
-- use work.${packageName}.all;
--
-- # Then you have to set the connection between the flip flops and the mirror
-- # signals:     (this is used to determine the flipped signals)
-- # ! NOTE: this is not neccessary, if you use the modified std_cell
-- process begin
--   for i in 0 to N_FLIPFLOPS-1 loop
--     nc_mirror( "${packageName}.flipflop_mirror[" & integer'image(i) & "]", getFlipFlop(i) );
--   end loop;
-- end process;
--
-- # And finally do the SEU somewhere in your testbench:
-- sim_SEU_FF( FF_ID_to_test, clk, clk_period, seu_FF );
--
-- # The parameters are the following:
-- #   FF_ID_to_test: The integer ID of the flip flop to test.
-- #   SEU_active:    High while the SEU is active.
-- #   clk:           The clock driving this flip flop.
-- #   clk_period:    Clock period of this clock.
-- #   seu_FF:        An optional flag, indication if a modified std_cell with
-- #                  a SEU register for switching the value should be used.
--

library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;

-- we want to change signals inside the hierachy, not only the top module
-- (only works with cadence tools)
library NCUTILS;
use NCUTILS.ncutilities.all;


package $packageName is
  constant N_FLIPFLOPS      : integer := $nFF;
  constant duration_glitch  : time := 100 ps;
  signal   flipflop_mirror  : std_logic_vector(N_FLIPFLOPS-1 downto 0);

  -- Simulate a single event upset for a flip flop
  procedure sim_SEU_FF (
    constant src    : in  integer range 0 to N_FLIPFLOPS-1; -- which FF to use?
    signal   seu    : out std_logic;        -- SEU active
    signal   clk    : in  std_logic;        -- clock
    constant clk_p  : in  time;             -- clock period
    constant seu_FF : in  std_logic := '0'  -- use the modified std_cells with SEU flag
  );

  -- Produce the acutal glitch
  procedure produce_SEU_glitch (
    constant src : in string;           -- the source we are testing
    constant sig : in string;           -- a copy of the source
    constant ver : in string := ""      -- ? "" : "verbose"
  );

  -- get a flip flop name and path by its ID
  function getFlipFlop( n : in integer, seu_FF : in std_logic ) return string;
end;

package body $packageName is

  -- Simulate single event upsets for a flip flop
  procedure sim_SEU_FF (
    constant src    : in  integer range 0 to N_FLIPFLOPS-1; -- which FF to use?
    signal   seu    : out std_logic;        -- SEU active
    signal   clk    : in  std_logic;        -- clock
    constant clk_p  : in  time;             -- clock period
    constant seu_FF : in  std_logic := '0'  -- use the modified std_cells with SEU flag
  ) is
    variable flipped_signal : string( 1 to 3 );
  begin
    wait until rising_edge(clk);
    if seu_FF = '1' then
      -- make the SEU appear in the middle of the high phase
      wait for clk_p/4;
    else
      -- make the SEU appear on a rising edge of the clock
      wait for (clk_p - duration_glitch/2);
    end if

    if seu_FF = '1' then
      flipped_signal := "'b1";
    elsif flipflop_mirror(src) = '1' then
      flipped_signal := "'b0";
    else
      flipped_signal := "'b1";
    end if;

    produce_SEU_glitch(getFlipFlop(src, seu_FF), flipped_signal);
  end procedure;


  -- Produce the acutal glitch
  procedure produce_SEU_glitch (
    constant src : in string;           -- the source we are testing
    constant sig : in string;           -- a copy of the source
    constant ver : in string := ""      -- ? "" : "verbose"
  ) is
  begin
    -- change the value
    nc_force( source => src, value => sig, verbose => ver );

    -- enforce the value for a short time
    wait for duration_glitch;

    -- let the modules deal with whatever they do with that
    nc_release( source => src, keepvalue => "", verbose => ver );
  end procedure;


  -- get a flip flop name and path by its ID
  function getFlipFlop( n : in integer, seu_FF : in std_logic )
  return string is
  begin
    if seu_FF = '1' then
      -- the variant with the modified std_cell, that has a SEU flag inside the FF
      case n is
        #for $ff in $flipflops_SEU
        when $flipflops_SEU.index($ff) => return "$ff";
        #end for
        when others => return "NOT FOUND";
      end case;




    else
      -- the default version, without the additional SEU flag
      case n is
        #for $ff in $flipflops
        when $flipflops.index($ff) => return "$ff";
        #end for
        when others => return "NOT FOUND";
      end case;
    end if;
  end getFlipFlop;
end package body;
