dat = read.csv('poc_bench.csv', header=T)
len = length(dat$num)
od = sort(dat$od)
poc = sort(dat$poc)
version1 = sort(dat$version1)
plot(seq(length(od)), od,
     type='l',
     log='y',
     col='red',
     xlim=c(0,len),
     ylim=c(1e-3,2),
     xlab='Instance',
     ylab='Time (s)')
lines(seq(length(poc)), poc, col='blue')
lines(seq(length(version1)), version1, col='green')
abline(h=c(0.01, 0.1, 1,2), untf=T, col='lightgrey')
