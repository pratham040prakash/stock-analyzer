process.env.APEX_CAPITAL_SELF_CHECK = "1";

import "../lib/dailyLoop/capitalDecision";
import { runCapitalProjectionSelfCheck } from "../lib/dailyLoop/capitalProjection";
import { runCapitalFinalStateSelfCheck } from "../lib/dailyLoop/capitalFinalState";
import { runCapitalDecisionLockSelfCheck } from "../lib/dailyLoop/capitalDecisionLock";
import { runCapitalMarginSelfCheck } from "../lib/dailyLoop/capitalMargin";
import { runTodaySurfaceSelfCheck } from "../lib/dailyLoop/todaySurface";
import { runZerodhaFundsSelfCheck } from "../lib/broker/zerodhaFunds";
import { runCommitmentSelfCheck } from "../lib/dailyLoop/disciplineCommitment";
import { runDisciplineHistoryMergeSelfCheck } from "../lib/dailyLoop/disciplineHistoryMerge";

runCapitalProjectionSelfCheck();
runCapitalFinalStateSelfCheck();
runCapitalDecisionLockSelfCheck();
runCapitalMarginSelfCheck();
runTodaySurfaceSelfCheck();
runZerodhaFundsSelfCheck();
runCommitmentSelfCheck();
runDisciplineHistoryMergeSelfCheck();
