// Created by ihdl
`timescale 1ns/10ps

module DFFR (Q,QBAR,CLK,D,RN,notifier);

  output  Q;
  output  QBAR;
  input   CLK;
  input   D;
  input   RN;
  input   notifier;

  // These lines have been added to enable a simulation of a SEU
  reg SEU = 1'b0;
  always @(posedge CLK) begin
    SEU <= 1'b0;
  end

  wire qout, qout2;
  assign qout2 = (SEU) ? ~qout : qout;
  // end of new lines

  DFF_ASYNR  r1 (qout,CLK,D,RN,notifier);
  buf        b0 (Q, qout2);     // changed from qout to qout2
  not        i1 (QBAR, qout2);  // changed from qout to qout2

endmodule
