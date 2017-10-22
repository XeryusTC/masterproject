file = rev(list.files('results', 'benchmark*'))[1]
dat = read.csv(paste('results/', file, sep=""), header=T)

algorithms = c("OD.ID", "Naive", "Base.version", "Version.1b", "Window.2", "Window.4", "Window.8")
cannonical_names = c("OD+ID", "NPPCPF", "PPCPF", "PPCPF+", "WPPCPF-2", "WPPCPF-4", "WPPCPF-8")
color_set = c("red", "blue", "green", "grey", "magenta", "cyan", "orange")

len = length(dat$instance)
od = sort(dat$OD.ID * 1000)
naive = sort(dat$Naive * 1000)
base = sort(dat$Base.version * 1000)
baseb = sort(dat$Version.1b * 1000)
window2 = sort(dat$Window.2 * 1000)
window4 = sort(dat$Window.4 * 1000)
window8 = sort(dat$Window.8 * 1000)

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
       legend=cannonical_names,
       col=color_set,
       pch=16)

solved = apply(dat[algorithms], 2, function(col)1-sum(is.na(col))/length(col))
bp = barplot(solved * 100,
        names.arg=cannonical_names,
        cex.names = .8,
        xlab='Algorithm',
        ylab='Percentage solved',
        ylim=c(0,100),
        col=color_set)
text(x = bp, y=solved * 100, xpd=T, label=solved*100, pos=3, cex=.8)

lengths = apply(dat[paste(algorithms, "length", sep="_")],
                2,
                function(col)mean(col-dat$optimal.length,na.rm=T))
bp2 = barplot(lengths,
              names.arg=cannonical_names,
              col=color_set,
              cex.names = .8,
              xlab='Algorithm',
              ylab='Mean path length')

# percentage that OD+ID is faster than Naive
mean(od < naive)

# Window statistics
dat.window = aggregate(cbind(dat$Window.2, dat$Window.4, dat$Window.8) ~ dat$num.agents, FUN=mean)
windowdat = rbind(cbind(dat$Window.2, 2), cbind(dat$Window.4, 4), cbind(dat$Window.8, 8))
lengthdat = rbind(cbind(dat$Window.2_length, 2), cbind(dat$Window.4_length, 4), cbind(dat$Window.8_length, 8))
anova(lm(windowdat[,1] ~ windowdat[,2]))
t.test(dat$Window.2, dat$Window.4)
t.test(dat$Window.2, dat$Window.8)
t.test(dat$Window.4, dat$Window.8)
anova(lm(lengthdat[,1] ~ lengthdat[,2]))
t.test(dat$Window.2_length, dat$Window.4_length)
t.test(dat$Window.2_length, dat$Window.8_length)
t.test(dat$Window.4_length, dat$Window.8_length)
