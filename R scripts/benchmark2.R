require(plyr)

file = rev(list.files('results', 'benchmark*'))[1]
dat = read.csv(paste('results/', file, sep=""), header=T)

algorithms = c("ODID", "Naive", "Base", "Plus", "Window2", "Window4", "Window8")
cannonical_names = c("OD+ID", "NPPCPF", "PPCPF", "PPCPF+", "WPPCPF-2", "WPPCPF-4", "WPPCPF-8")
color_set = c("red", "blue", "green", "grey", "magenta", "cyan", "orange")

len = length(unique(dat$instance))
od      = sort(dat[dat$algorithm=='ODID',]$time * 1000)
naive   = sort(dat[dat$algorithm=='Naive',]$time * 1000)
base    = sort(dat[dat$algorithm=='Base',]$time * 1000)
plus    = sort(dat[dat$algorithm=='Plus',]$time * 1000)
window2 = sort(dat[dat$algorithm=='Window2',]$time * 1000)
window4 = sort(dat[dat$algorithm=='Window4',]$time * 1000)
window8 = sort(dat[dat$algorithm=='Window8',]$time * 1000)

plot(1,
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
lines(seq(length(plus)),  plus,  col='grey')
lines(seq(length(window2)), window2, col='magenta')
lines(seq(length(window4)), window4, col='cyan')
lines(seq(length(window8)), window8, col='orange')
legend("bottomright",
       legend=cannonical_names,
       col=color_set,
       pch=16)

#solved = apply(dat[algorithms], 2, function(col)1-sum(is.na(col))/length(col))
dat.sub = subset(dat, !is.na(time))
solved = count(dat.sub$algorithm)$freq / count(dat[dat$algorithm != 'optimal',]$algorithm)$freq
bp = barplot(solved * 100,
        names.arg=cannonical_names,
        cex.names = .8,
        xlab='Algorithm',
        ylab='Percentage solved',
        ylim=c(0,100),
        col=color_set)
text(x = bp, y=solved * 100, xpd=T, label=solved*100, pos=3, cex=.8)

solved.aggr = aggregate(time ~ factor(algorithm, levels=algorithms) + num.agents, data=dat,
                        FUN=function(x)1-sum(is.na(x))/length(x),
                        na.action=na.pass)
plot(1,
     type='l',
     xlim=c(0,40),
     ylim=c(0,1),
     xlab='Number of agents',
     ylab='Percentage solved',
     frame.plot = F
)
for(i in 1:length(algorithms))
{
    lines(solved.aggr[solved.aggr[,1]==algorithms[i],]$time, col=color_set[i])
}
legend("bottomleft",
       legend=cannonical_names,
       col=color_set,
       pch=16)

lengths = aggregate(length ~ factor(algorithm, levels=algorithms), data=dat, FUN=mean)
bp2 = barplot(lengths$length,
              names.arg=cannonical_names,
              col=color_set,
              cex.names = .8,
              xlab='Algorithm',
              ylab='Mean path length')

# percentage that OD+ID is faster than Naive
naive.vs.odid = mean(dat[dat$algorithm=="ODID","time"] < dat[dat$algorithm=="Naive","time"], na.rm=T)

base.vs.plus = t.test(dat[dat$algorithm=="Base","time"],
                      dat[dat$algorithm=="Plus","time"],
                      paired=T, alternative = "less")

# Window statistics
windowdat = subset(dat, algorithm %in% c("Window2", "Window4", "Window8"))
w.anova = anova(lm(windowdat$time ~ windowdat$algorithm + windowdat$num.agents))
t.2vs4 = t.test(log(dat[dat$algorithm=="Window2","time"]),
                log(dat[dat$algorithm=="Window4","time"]))
t.2vs8 = t.test(log(dat[dat$algorithm=="Window2","time"]),
                log(dat[dat$algorithm=="Window8","time"]))
t.4vs8 = t.test(log(dat[dat$algorithm=="Window4","time"]),
                log(dat[dat$algorithm=="Window8","time"]))
#t.2vs8 = t.test(dat$Window.2, dat$Window.8)
#t.4vs8 = t.test(dat$Window.4, dat$Window.8)
