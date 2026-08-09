process.env.APEX_CAPITAL_SELF_CHECK = "1";

import "../lib/dailyLoop/capitalDecision";
import { runCapitalProjectionSelfCheck } from "../lib/dailyLoop/capitalProjection";
import { runCapitalFinalStateSelfCheck } from "../lib/dailyLoop/capitalFinalState";
import { runCapitalDecisionLockSelfCheck } from "../lib/dailyLoop/capitalDecisionLock";

runCapitalProjectionSelfCheck();
runCapitalFinalStateSelfCheck();
runCapitalDecisionLockSelfCheck();
