#################################################### 
                     ## Clock #
####################################################

create_clock -period 5.500 -name i_clk -waveform {0.000 2.750} [get_ports i_clk]

##Frequency: 50MHZ
##Duty Circle: 50%