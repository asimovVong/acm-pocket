import test from 'node:test';
import assert from 'node:assert/strict';
import { shelfSteps, segmentSums, balancedCuts } from '../models.mjs';
test('shelf demonstration includes the head position and distinguishes duplicates', () => {
  assert.deepEqual(shelfSteps([1,2,3],1).map(x=>[x.right,x.choices,x.answer]), [[2,2,2],[3,2,4],[3,1,4]]);
  assert.equal(shelfSteps([4,4,4],10).at(-1).answer,6);
  assert.equal(shelfSteps([8,1],1).at(-1).answer,1);
});
test('middle cut demonstration agrees with all admissible cuts on short arrays', () => {
  for(let n=4;n<=8;n++) for(let mask=0;mask<2**n;mask++) {
    const a=Array.from({length:n},(_,i)=>(mask>>i&1)?7:1);
    for(let j=2;j<=n-2;j++) {
      let best=Infinity;
      for(let l=1;l<j;l++) for(let r=j+1;r<n;r++) {
        const v=segmentSums(a,[l,j,r]); best=Math.min(best,Math.max(...v)-Math.min(...v));
      }
      const v=segmentSums(a,balancedCuts(a,j));
      assert.equal(Math.max(...v)-Math.min(...v),best,`${a} middle=${j}`);
    }
  }
});
