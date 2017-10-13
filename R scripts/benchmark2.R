require(tikzDevice)

file = rev(list.files('results', 'benchmark*'))[1]
dat = read.csv(paste('results/', file, sep=""), header=T)

algorithms = c("OD.ID", "Naive", "Base.version", "Version.1b", "Window.2", "Window.4", "Window.8")
cannonical_names = c("OD+ID", "Naive", "Base", "Base+", "Window 2", "Window 4", "Window 8")
color_set = c("red", "blue", "green", "grey", "magenta", "cyan", "orange")

len = length(dat$instance)
od = sort(dat$OD.ID * 1000)
naive = sort(dat$Naive * 1000)
base = sort(dat$Base.version * 1000)
baseb = sort(dat$Version.1b * 1000)
window2 = sort(dat$Window.2 * 1000)
window4 = sort(dat$Window.4 * 1000)
window8 = sort(dat$Window.8 * 1000)

tikz('reports/final/graphs/perfgraph.tex', standAlone=F, width=5, height=3)
plot(c(), c(),
	 type='l',
	 log='y',
	 col='red',
	 xlim=c(1,len),
	 ylim=c(5, 2000),
	 xlab='Instance',
	 ylab='Time (ms)',
	 frame.plot=F
)
lines(seq(length(od)), od, col='red')
lines(seq(length(naive)), naive, col='blue')
lines(seq(length(base)),  base,  col='green')
lines(seq(length(baseb)), baseb, col='grey')
lines(seq(length(window2)), window2, col='magenta')
lines(seq(length(window4)), window4, col='cyan')
lines(seq(length(window8)), window8, col='orange')
legend("bottomright",
       legend=c("OD+ID", "Naive", "Base", "Base+", "Window 2", "Window 4", "Window 8"),
       col=color_set,
       pch=16)
dev.off()

tikz('reports/final/graphs/solved.tex', width=5, height=3)
solved = apply(dat[algorithms], 2, function(col)1-sum(is.na(col))/length(col))
bp = barplot(solved * 100,
        names.arg=cannonical_names,
        cex.names = .8,
        xlab='Algorithm',
        ylab='Percentage solved',
        ylim=c(0,100),
        col=color_set)
text(x = bp, y=solved * 100, xpd=T, label=solved*100, pos=3, cex=.8)
dev.off()

tikz('reports/final/graphs/lengths.tex', width=5, height=3)
lengths = apply(dat[paste(algorithms, "length", sep="_")],
                2,
                function(col)mean(col-dat$optimal.length,na.rm=T))
bp2 = barplot(lengths,
              names.arg=cannonical_names,
              col=color_set,
              cex.names = .8,
              xlab='Algorithm',
              ylab='Mean path length')
dev.off()

#lengths = aggregate(cbind(optimal.length, OD.ID_length, Naive_length, Base.version_length, Version.1b_length, Window.2_length, Window.4_length, Window.8_length) ~ num.agents, data=dat, FUN=mean)
#makespans = aggregate(cbind(optimal.makespan, OD.ID_makespan, Naive_makespan, Base.version_makespan, Version.1b_makespan, Window.2_makespan, Window.4_makespan, Window.8_makespan) ~ num.agents, data=dat, FUN=mean)