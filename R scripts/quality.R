file = rev(list.files('results', 'quality*'))[1]
quality.dat = read.csv(paste('results/', file, sep=""), header=T)

algorithms = c("ODID", "Naive", "Base", "Plus", "Window2", "Window4",
               "Window8", "DiMPP")
cannonical_names = c("OD+ID", "NPPCPF", "PPCPF", "PPCPF+", "WPPCPF-2",
                     "WPPCPF-4", "WPPCPF-8", "DiMPP")
color_set = c("red", "blue", "green", "grey", "magenta", "cyan", "orange",
              "purple")

quality.aggr = aggregate(cbind(length, loops) ~ num.agents + algorithm, FUN=mean,
                         data=quality.dat)

plot(1,
     xlim=c(0,40),
     ylim=c(0,1),
     xlab="Number of agents",
     ylab="Number of loops",
     frame.plot=F,
     type='n')
quality.aggr[quality.aggr[,2]==algorithms[1],]
for(i in 1:7) {
    lines(quality.aggr[quality.aggr[,2]==algorithms[i],]$loops, col=color_set[i])
}
legend("topleft",
       legend=cannonical_names[5:7],
       col=color_set[5:7],
       pch=16)
