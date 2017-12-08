file = rev(list.files('results', 'conflictsize-*'))[1]
sizes.dat = read.csv(paste('results/', file, sep=""), header=T)

sizes.aggr = aggregate(cbind(X2, X3, X4, X5) ~ num.agents, data=sizes.dat, FUN=mean)

plot(1,
     type='n',
     xlim=c(1,31),
     ylim=c(0.01,15),
     xlab="Number of agents",
     ylab="Numbor of conflicts",
     yaxs="i",
     frame.plot = F
     )
points(sizes.aggr$X2[1:31], col='red', pch=8)
points(sizes.aggr$X3, col='blue', pch=4)
points(sizes.aggr$X4, col='green', pch=3)
lines(smooth.spline(sizes.aggr$X2[1:31], spar=0.35), col="red")
lines(smooth.spline(sizes.aggr$X3[1:31], spar=0.35), col="blue")
lines(smooth.spline(sizes.aggr$X4, spar=0.35), col="green")
legend("topleft",
       legend=c('2 agents', '3 agents', '4 agents'),
       col=c("red", "blue", "green"),
       pch=c(8, 4, 3), bty='n')
