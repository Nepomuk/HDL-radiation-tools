--------------------------------------------------------------------------------
-- Author:   André Goerres (FZ Jülich) - a.goerres@fz-juelich.de
--
-- Create Date:  2014-02-14
-- Design Name:  hamming_components
-- Description:  This collection contains modules converting signals
--               to Hamming Code. In detail there are:
--                - a Hamming Register (storing data Hamming encoded)
--                - a Hamming Encoder  (plain to Hamming Code)
--                - a Hamming Decoder  (Hamming Code to plain)
--                - a Hamming Counter  (internal counting with Hamming Code)
--               All of these modules are generic and need the length of
--               raw (NBits) and encoded (NBitsEnc) data vectors.
--
--------------------------------------------------------------------------------


--------------------------------------------------------------------------------
--  Generic Hamming Register
--------------------------------------------------------------------------------

library IEEE;
use IEEE.std_logic_1164.all;
use IEEE.numeric_std.all;


entity HammingRegister is
  generic (
    NBits     : integer := 4;
    NBitsEnc  : integer := 7
  );
  port (
    clk       : in  std_logic;
    nreset    : in  std_logic;
    data_in   : in  std_logic_vector(NBits-1 downto 0);
    data_out  : out std_logic_vector(NBits-1 downto 0);
    SEU_error : out std_logic
  );
end HammingRegister;

architecture HammingRegister_RTL of HammingRegister is

  component HammingEncoder
    generic (
      NBits     : integer;
      NBitsEnc  : integer
    );
    port (
      data_in   : in  std_logic_vector(NBits-1 downto 0);
      data_enc  : out std_logic_vector(NBitsEnc-1 downto 0)
    );
  end component;

  component HammingDecoder
    generic (
      NBits     : integer;
      NBitsEnc  : integer
    );
    port (
      data_enc  : in  std_logic_vector(NBitsEnc-1 downto 0);
      data_out  : out std_logic_vector(NBits-1 downto 0);
      SEU_error : out std_logic
    );
  end component;

  signal register_enc      : std_logic_vector(NBitsEnc-1 downto 0);
  signal register_ham      : std_logic_vector(NBitsEnc-1 downto 0);

begin

  encoder : HammingEncoder
  generic map (
    NBits     => NBits,
    NBitsEnc  => NBitsEnc
  )
  port map (
    data_in   => data_in,
    data_enc  => register_enc
  );
  decoder : HammingDecoder
  generic map (
    NBits     => NBits,
    NBitsEnc  => NBitsEnc
  )
  port map (
    data_enc  => register_ham,
    data_out  => data_out,
    SEU_error => SEU_error
  );
  process (clk, nreset) begin
    if nreset = '0' then
      register_ham <= (others => '0');
    elsif rising_edge(clk) then
      register_ham <= register_enc;
    end if;
  end process;

end HammingRegister_RTL;



--------------------------------------------------------------------------------
--  Generic Hamming Encoder
--------------------------------------------------------------------------------

library IEEE;
use IEEE.std_logic_1164.all;
use IEEE.numeric_std.all;


entity HammingEncoder is
  generic (
    NBits     : integer := 4;
    NBitsEnc  : integer := 7
  );
  port (
    data_in   : in  std_logic_vector(NBits-1 downto 0);
    data_enc  : out std_logic_vector(NBitsEnc-1 downto 0)
  );
end HammingEncoder;

architecture HammingEncoder_RTL of HammingEncoder is

  constant NParity   : integer := NBitsEnc - NBits;

  -- Get the parity index for the current position if this is a parity bit
  function getParityIndex(pos : integer)
    return integer is
    variable pos_slv  : std_logic_vector(NParity-1 downto 0);
    variable count    : integer range 0 to NBitsEnc := 0;
    variable position : integer range 0 to NParity-1 := 0;
  begin
    -- if this is a parity position, the position as slv would only have one bit set
    -- (like 001, 010, 100 but not 011)
    pos_slv := std_logic_vector(to_unsigned(pos+1, pos_slv'length));
    for i in pos_slv'range loop
      if pos_slv(i) = '1' then
        count := count + 1;
        position := i;
      end if;
    end loop;

    if count = 1 then
      return position+1;
    else
      return 0;
    end if;
  end getParityIndex;

  -- Is the current bit a parity bit?
  -- (basically getParityIndex, should enhance readability)
  function isParityPosition(pos : integer)
    return boolean is
  begin
    return getParityIndex(pos) > 0;
  end isParityPosition;


  -- Similar to getParityIndex, this function delivers the data index for the
  -- current position.
  function getDataIndex(pos : integer)
    return integer is
    variable pos_slv          : std_logic_vector(NParity-1 downto 0);
    variable lastParityIndex  : integer range 0 to NParity;
  begin
    pos_slv := std_logic_vector(to_unsigned(pos+1, pos_slv'length));
    lastParityIndex := 0;
    for i in NParity-1 downto 0 loop
      if pos_slv(i) = '1' and lastParityIndex = 0 then
        lastParityIndex := i+1;
      end if;
    end loop;

    -- This functions gets called even when it is a parity index. Make sure that
    -- we don't screw up the index range with a negative output
    if lastParityIndex > pos then
      return 0;
    else
      return pos - lastParityIndex;
    end if;
  end getDataIndex;


  -- Calculate the parity of the given index from the data
  function getParity(curIndex : integer; data : std_logic_vector)
    return std_logic is
    variable pos_slv  : std_logic_vector(NParity-1 downto 0);
    variable temp     : std_logic;
  begin
    temp := '0';
    for i in curIndex+1 to NBitsEnc-1 loop
      pos_slv := std_logic_vector(to_unsigned(i+1, pos_slv'length));
      if pos_slv(getParityIndex(curIndex)-1) = '1' then
        temp := temp xor data(i);
      end if;
    end loop;
    return temp;
  end getParity;

  signal data_int   : std_logic_vector(NBitsEnc-1 downto 0);

begin

  encoder : for i in 0 to NBitsEnc-1 generate
    data_int(i) <= getParity(i, data_int) when isParityPosition(i) else data_in(getDataIndex(i));
  end generate;

  data_enc <= data_int;

end HammingEncoder_RTL;



--------------------------------------------------------------------------------
--  Generic Hamming Decoder
--------------------------------------------------------------------------------

library IEEE;
use IEEE.std_logic_1164.all;
use IEEE.numeric_std.all;


entity HammingDecoder is
  generic (
    constant NBits    : integer := 4;
    constant NBitsEnc : integer := 7
  );
  port (
    data_enc  : in  std_logic_vector(NBitsEnc-1 downto 0);
    data_out  : out std_logic_vector(NBits-1 downto 0);
    SEU_error : out std_logic
  );
end HammingDecoder;

architecture HammingDecoder_RTL of HammingDecoder is

  constant NParity   : integer := NBitsEnc - NBits;

  -- Calculate the parity of the given index from the data
  function getParity(parityIndex : integer; data : std_logic_vector)
    return std_logic is
    variable pos_slv  : std_logic_vector(NParity-1 downto 0);
    variable temp     : std_logic;
  begin
    temp := '0';
    for i in 0 to NBitsEnc-1 loop
      pos_slv := std_logic_vector(to_unsigned(i+1, pos_slv'length));
      if pos_slv(parityIndex) = '1' then
        temp := temp xor data(i);
      end if;
    end loop;
    return temp;
  end getParity;


  -- Get the parity index for the current position if this is a parity bit
  function getParityIndex(pos : integer)
    return integer is
    variable pos_slv  : std_logic_vector(NParity-1 downto 0);
    variable count    : integer range 0 to NBitsEnc := 0;
    variable position : integer range 0 to NParity-1 := 0;
  begin
    -- if this is a parity position, the position as slv would only have one bit set
    -- (like 001, 010, 100 but not 011)
    pos_slv := std_logic_vector(to_unsigned(pos+1, pos_slv'length));
    for i in pos_slv'range loop
      if pos_slv(i) = '1' then
        count := count + 1;
        position := i;
      end if;
    end loop;

    if count = 1 then
      return position+1;
    else
      return 0;
    end if;
  end getParityIndex;

  -- Is the current bit a parity bit?
  -- (basically getParityIndex, should enhance readability)
  function isParityPosition(pos : integer)
    return boolean is
  begin
    return getParityIndex(pos) > 0;
  end isParityPosition;

  function extractDataBit(dataIndex : integer; dataEnc : std_logic_vector; correction : std_logic_vector)
    return std_logic is
    variable dataBitCounter : integer;
    variable dataBit        : std_logic;
  begin
    dataBitCounter := 0;
    for i in 0 to dataEnc'length-1 loop
      if not isParityPosition(i) then
        if dataBitCounter = dataIndex then
          dataBit := dataEnc(i) xor correction(i);
        end if;
        dataBitCounter := dataBitCounter + 1;
      end if;
    end loop;
    return dataBit;
  end extractDataBit;

  -- repeated 'or' function for a slv with an arbitrary length
  function all_zeros ( slv : std_logic_vector )
  return std_logic is
    variable result : std_logic;
  begin
    result := '0';
    for i in slv'range loop
      result := result or slv(i);
    end loop;
    return not result;
  end all_zeros;

  signal parity_out : std_logic_vector(NParity-1 downto 0);
  signal correction : std_logic_vector(NBitsEnc-1 downto 0);

begin

  -- Hamming output decoding
  dataExtraction_generator : for i in 0 to NBits-1 generate
    data_out(i) <= extractDataBit(i, data_enc, correction);
  end generate;


  -- Hamming parity bits at the output
  parity_generator : for i in 0 to NParity-1 generate
    parity_out(i) <= getParity(i, data_enc);
  end generate;

  SEU_error <= not all_zeros(parity_out);


  -- Hamming correction word
  correction_generator : for i in correction'range generate
    correction(i) <= '1' when to_integer(unsigned(parity_out))-1 = i else '0';
  end generate;

end HammingDecoder_RTL;




--------------------------------------------------------------------------------
--  Generic Hamming Counter
--------------------------------------------------------------------------------

library IEEE;
use IEEE.std_logic_1164.all;
use IEEE.numeric_std.all;


entity HammingCounter is
  generic (
    NBits       : integer := 4;
    NBitsEnc    : integer := 7 );
  port (
    nreset      : in  std_logic;
    clock       : in  std_logic;
    enable      : in  std_logic;
    count_out   : out std_logic_vector(NBits-1 downto 0);
    endofcount  : out std_logic;
    SEU_error   : out std_logic);
end HammingCounter;

architecture HammingCounter_RTL of HammingCounter is

  -- repeated 'and' function for a slv with an arbitrary length
  function all_ones ( slv : std_logic_vector )
  return boolean is
    variable result : std_logic;
  begin
    result := '1';
    for i in slv'range loop
      result := result and slv(i);
    end loop;
    return result = '1';
  end all_ones;

  signal ctr_int      : unsigned(NBits-1 downto 0);
  signal ctr_new_int  : unsigned(NBits-1 downto 0);
  signal ctr_decoded  : std_logic_vector(NBits-1 downto 0);
  signal ctr_new      : std_logic_vector(NBits-1 downto 0);
  signal ctr_encoded  : std_logic_vector(NBitsEnc-1 downto 0);
  signal hamming_reg  : std_logic_vector(NBitsEnc-1 downto 0);

  component HammingEncoder
    port (
      data_in   : in  std_logic_vector(NBits-1 downto 0);
      data_enc  : out std_logic_vector(NBitsEnc-1 downto 0)
    );
  end component;

  component HammingDecoder
    port (
      data_enc  : in  std_logic_vector(NBitsEnc-1 downto 0);
      data_out  : out std_logic_vector(NBits-1 downto 0);
      SEU_error : out std_logic
    );
  end component;

begin

  input_encoder : HammingEncoder
  port map (
    data_in   => ctr_new,
    data_enc  => ctr_encoded
  );

  output_decoder : HammingDecoder
  port map (
    data_enc  => hamming_reg,
    data_out  => ctr_decoded,
    SEU_error => SEU_error
  );

  ctr_int     <= unsigned(ctr_decoded);
  ctr_new_int <= ctr_int + 1 when enable = '1' else ctr_int;
  ctr_new     <= std_logic_vector(ctr_new_int);

  count_process : process(nreset,clock)
  begin
    if (nreset = '0') then
      hamming_reg <= (others => '0');
    elsif rising_edge(clock) then
      hamming_reg <= ctr_encoded;
    end if;
  end process;
  count_out <= ctr_decoded;
  endofcount <= '1' when all_ones(ctr_decoded) else '0';

end HammingCounter_RTL;


